import os
import numpy as np
import uuid
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, BinaryIO
from tempfile import NamedTemporaryFile

from app.cv.pet_finder import SimplePetFinder
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class CVService:
    def __init__(self):
        self.pet_finder = SimplePetFinder()
        self.detection_threshold = getattr(settings, "CV_DETECTION_THRESHOLD", 0.5)
        self.similarity_threshold = getattr(settings, "CV_SIMILARITY_THRESHOLD", 0.6)
        self.default_weights = {
            "visual": getattr(settings, "CV_WEIGHT_VISUAL", 0.6),
            "attribute": getattr(settings, "CV_WEIGHT_ATTRIBUTE", 0.2),
            "location": getattr(settings, "CV_WEIGHT_LOCATION", 0.1),
            "time": getattr(settings, "CV_WEIGHT_TIME", 0.1),
        }
        logger.info("CVService initialized with pet finder")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image to detect pets and their attributes

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with detected animals information and processing time
        """
        start_time = time.time()
        try:
            logger.info(f"Analyzing image at path: {image_path}")
            cropped_pet, pet_class, attributes = self.pet_finder.detect_pet(image_path)

            if cropped_pet is None:
                logger.warning(f"No animals detected in image: {image_path}")
                return {"detected_animals": [], "processing_time_ms": 0}

            bounding_box = [0, 0, cropped_pet.width, cropped_pet.height]

            processing_time = int((time.time() - start_time) * 1000)  # Convert to ms

            result = {
                "detected_animals": [
                    {
                        "species": pet_class,
                        "confidence": (
                            attributes.get("confidence", 0.0) if attributes else 0.0
                        ),
                        "bounding_box": bounding_box,
                        "attributes": attributes or {},
                    }
                ],
                "processing_time_ms": processing_time,
            }
            logger.info(f"Successfully analyzed image: {image_path}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {str(e)}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            return {
                "error": str(e),
                "detected_animals": [],
                "processing_time_ms": processing_time,
            }

    def analyze_image_content(self, image_content: BinaryIO) -> Dict[str, Any]:
        """
        Analyze an image from file content instead of a file path

        Args:
            image_content: File-like object containing image data

        Returns:
            Dictionary with detected animals information and processing time
        """
        with NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_path = temp_file.name
            image_content.seek(0)
            temp_file.write(image_content.read())

        try:
            result = self.analyze_image(temp_path)
            return result
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def compare_images(
        self,
        source_features: bytes,
        target_features_list: List[bytes],
        source_attrs: Optional[Dict] = None,
        target_attrs_list: Optional[List[Dict]] = None,
        location_data: Optional[Dict] = None,
        date_data: Optional[Dict] = None,
        feature_weights: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Compare a source image against multiple target images

        Args:
            source_features: Feature vector for source image
            target_features_list: List of feature vectors for target images
            source_attrs: Attributes for source image
            target_attrs_list: List of attributes for target images
            location_data: Dictionary with source and target location information
            date_data: Dictionary with source and target date information
            feature_weights: Dictionary with weights for each component

        Returns:
            Dictionary with comparison results and metadata
        """
        start_time = time.time()

        if not source_features or not target_features_list:
            logger.warning("Empty source features or target features list")
            return {
                "comparisons": [],
                "search_metadata": {
                    "total_candidates_considered": (
                        len(target_features_list) if target_features_list else 0
                    ),
                    "filtered_candidates": 0,
                    "processing_time_ms": 0,
                    "search_radius_expanded": False,
                    "error_occurred": True,
                    "error": "Empty source features or target features list",
                },
            }

        if feature_weights is None:
            feature_weights = self.default_weights.copy()

        for component in ["visual", "attribute", "location", "time"]:
            if component not in feature_weights:
                feature_weights[component] = self.default_weights.get(component, 0.25)

        total_weight = sum(feature_weights.values())
        if total_weight != 1:
            for k in feature_weights:
                feature_weights[k] /= total_weight

        try:
            logger.info(
                f"Comparing source image against {len(target_features_list)} targets"
            )

            try:
                source_array = np.frombuffer(source_features, dtype=np.float32)
            except Exception as e:
                logger.error(f"Error converting source features to numpy array: {e}")
                raise ValueError(f"Invalid source feature vector format: {e}")

            target_arrays = []
            valid_indices = []

            for i, target_feature in enumerate(target_features_list):
                try:
                    target_array = np.frombuffer(target_feature, dtype=np.float32)
                    target_arrays.append(target_array)
                    valid_indices.append(i)
                except Exception as e:
                    logger.error(
                        f"Error converting target feature {i} to numpy array: {e}"
                    )

            if not target_arrays:
                logger.warning("No valid target feature vectors")
                return {
                    "comparisons": [],
                    "search_metadata": {
                        "total_candidates_considered": len(target_features_list),
                        "filtered_candidates": 0,
                        "processing_time_ms": int((time.time() - start_time) * 1000),
                        "search_radius_expanded": False,
                        "error_occurred": True,
                        "error": "No valid target feature vectors",
                    },
                }

            comparisons = []
            for i, target_array in enumerate(target_arrays):
                orig_idx = valid_indices[i]

                target_attrs = (
                    target_attrs_list[orig_idx]
                    if target_attrs_list and orig_idx < len(target_attrs_list)
                    else None
                )

                location1 = location2 = None
                if (
                    location_data
                    and "source" in location_data
                    and "targets" in location_data
                    and location_data["source"]
                ):
                    location1 = location_data["source"]
                    location2 = (
                        location_data["targets"][orig_idx]
                        if location_data["targets"]
                        and orig_idx < len(location_data["targets"])
                        else None
                    )

                date1 = date2 = None
                if date_data and "source" in date_data and "targets" in date_data:
                    date1 = date_data["source"]
                    date2 = (
                        date_data["targets"][orig_idx]
                        if date_data["targets"] and orig_idx < len(date_data["targets"])
                        else None
                    )

                try:
                    similarity = self.pet_finder.compare_pets(
                        source_array,
                        target_array,
                        source_attrs,
                        target_attrs,
                        location1,
                        location2,
                        date1,
                        date2,
                        weights=feature_weights,
                    )
                except Exception as e:
                    logger.error(f"Error comparing pets: {e}")
                    continue

                try:
                    matching_features = self.pet_finder.get_matching_features(
                        source_attrs, target_attrs
                    )
                except Exception as e:
                    logger.error(f"Error getting matching features: {e}")
                    matching_features = []

                if similarity["overall"] >= self.similarity_threshold:
                    comparisons.append(
                        {
                            "target_index": orig_idx,
                            "similarity": similarity,
                            "matching_features": matching_features,
                        }
                    )

            comparisons.sort(key=lambda x: x["similarity"]["overall"], reverse=True)

            processing_time = int((time.time() - start_time) * 1000)

            result = {
                "comparisons": comparisons,
                "search_metadata": {
                    "total_candidates_considered": len(target_features_list),
                    "filtered_candidates": len(comparisons),
                    "processing_time_ms": processing_time,
                    "search_radius_expanded": False,
                    "similarity_threshold": self.similarity_threshold,
                    "weights_used": feature_weights,
                },
            }
            logger.info(f"Image comparison completed with {len(comparisons)} matches")
            return result

        except Exception as e:
            logger.error(f"Error comparing images: {str(e)}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            return {
                "error": str(e),
                "comparisons": [],
                "search_metadata": {
                    "total_candidates_considered": (
                        len(target_features_list) if target_features_list else 0
                    ),
                    "filtered_candidates": 0,
                    "processing_time_ms": processing_time,
                    "search_radius_expanded": False,
                    "error_occurred": True,
                },
            }

    def format_api_results(
        self, lost_pet_path: str, matches: List, max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Format match results in a way compatible with the API structure

        Args:
            lost_pet_path: Path to the lost pet image
            matches: List of match information
            max_results: Maximum number of results to include

        Returns:
            Dictionary with formatted comparison results and metadata
        """
        start_time = time.time()
        try:
            logger.info(f"Formatting API results for {len(matches)} matches")
            results = []

            lost_pet_img, lost_pet_class, lost_pet_attributes = (
                self.pet_finder.detect_pet(lost_pet_path)
            )

            for i, match in enumerate(matches[:max_results]):
                similarity = (
                    match["similarity_scores"]
                    if "similarity_scores" in match
                    else {
                        "overall": match["similarity"],
                        "visual": match["similarity"],
                        "attribute": 0,
                        "location": 0,
                        "time": 0,
                    }
                )

                result = {
                    "target_image_id": os.path.basename(match["path"]),
                    "pet_id": str(uuid.uuid4()),
                    "similarity": similarity,
                    "matching_features": match.get("matching_features", []),
                    "pet_details": {
                        "species": match["pet_type"].capitalize(),
                        "breed": match.get("attributes", {})
                        .get("breed", {})
                        .get("name", "Unknown"),
                    },
                }

                results.append(result)

            processing_time = int((time.time() - start_time) * 1000)

            result = {
                "comparisons": results,
                "search_metadata": {
                    "total_candidates_considered": len(matches),
                    "filtered_candidates": len(results),
                    "processing_time_ms": processing_time,
                    "search_radius_expanded": False,
                },
            }
            logger.info(f"API results formatting completed with {len(results)} results")
            return result

        except Exception as e:
            logger.error(f"Error formatting API results: {str(e)}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            return {
                "error": str(e),
                "comparisons": [],
                "search_metadata": {
                    "total_candidates_considered": 0,
                    "filtered_candidates": 0,
                    "processing_time_ms": processing_time,
                    "search_radius_expanded": False,
                    "error_occurred": True,
                },
            }

    def find_potential_matches(
        self,
        pet_photo_id: str,
        feature_vector: bytes,
        attributes: Dict[str, Any],
        target_features: List[Tuple[str, bytes, Dict[str, Any]]],
        location_data: Optional[Dict] = None,
        date_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Find potential matches for a lost or found pet

        Args:
            pet_photo_id: ID of the source pet photo
            feature_vector: Feature vector of the source pet photo
            attributes: Attributes of the source pet
            target_features: List of tuples (id, feature_vector, attributes) for target photos
            location_data: Dictionary with location data
            date_data: Dictionary with date data

        Returns:
            Dictionary with match results and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Finding potential matches for pet photo {pet_photo_id}")

            target_ids = [t[0] for t in target_features]
            target_feature_vectors = [t[1] for t in target_features]
            target_attributes = [t[2] for t in target_features]

            comparison_results = self.compare_images(
                source_features=feature_vector,
                target_features_list=target_feature_vectors,
                source_attrs=attributes,
                target_attrs_list=target_attributes,
                location_data=location_data,
                date_data=date_data,
            )

            for comp in comparison_results.get("comparisons", []):
                target_idx = comp.get("target_index", 0)
                if 0 <= target_idx < len(target_ids):
                    comp["target_id"] = target_ids[target_idx]

            comparison_results.setdefault("search_metadata", {})[
                "source_id"
            ] = pet_photo_id

            processing_time = int((time.time() - start_time) * 1000)
            comparison_results["search_metadata"][
                "processing_time_ms"
            ] = processing_time

            logger.info(
                f"Found {len(comparison_results.get('comparisons', []))} potential matches"
            )
            return comparison_results

        except Exception as e:
            logger.error(f"Error finding potential matches: {str(e)}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            return {
                "error": str(e),
                "comparisons": [],
                "search_metadata": {
                    "source_id": pet_photo_id,
                    "total_candidates_considered": len(target_features),
                    "filtered_candidates": 0,
                    "processing_time_ms": processing_time,
                    "search_radius_expanded": False,
                    "error_occurred": True,
                },
            }
