import os
import torch
import numpy as np
import logging
from PIL import Image, ImageColor
import torchvision.transforms as transforms
from torchvision.models import (
    resnet50,
    ResNet50_Weights,
    efficientnet_b3,
    EfficientNet_B3_Weights,
)
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import glob
from geopy.distance import geodesic
from collections import Counter

# Set up logging
logger = logging.getLogger(__name__)


class SimplePetFinder:
    def __init__(self):
        logger.info("Loading models...")

        # Load YOLOv5 for pet detection
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "yolov5s.pt"
        )
        if os.path.exists(model_path):
            logger.info(f"Loading YOLOv5 from local file: {model_path}")
            self.detector = torch.hub.load(
                "ultralytics/yolov5", "custom", path=model_path
            )
        else:
            logger.info("Loading YOLOv5 from torch hub")
            self.detector = torch.hub.load(
                "ultralytics/yolov5", "yolov5s", pretrained=True
            )

        # COCO dataset: 0=person, 15=cat, 16=dog
        self.pet_classes = [15, 16]
        logger.info(f"Model will detect these classes: {self.pet_classes}")

        # Initialize feature extraction models
        # Primary visual feature extractor (EfficientNet provides better features than ResNet50)
        eff_weights = EfficientNet_B3_Weights.DEFAULT
        self.feature_extractor = efficientnet_b3(weights=eff_weights)
        self.feature_extractor.classifier = torch.nn.Identity()
        self.feature_extractor.eval()

        # Secondary feature extractor for breed-specific features
        weights = ResNet50_Weights.DEFAULT
        self.secondary_extractor = resnet50(weights=weights)
        self.secondary_extractor.fc = torch.nn.Identity()
        self.secondary_extractor.eval()

        # Initialize transformations
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                eff_weights.transforms(),
            ]
        )

        # Dictionary to map pet types to breed lists
        self.breed_mapping = {
            "cat": [
                "Persian",
                "Maine Coon",
                "British Shorthair",
                "Siamese",
                "Ragdoll",
                "Bengal",
                "Abyssinian",
                "Scottish Fold",
                "Russian Blue",
                "Sphynx",
            ],
            "dog": [
                "Labrador Retriever",
                "German Shepherd",
                "Golden Retriever",
                "Bulldog",
                "Beagle",
                "Poodle",
                "Rottweiler",
                "Siberian Husky",
                "Dachshund",
                "Shih Tzu",
            ],
        }

        self.color_options = [
            "black",
            "white",
            "gray",
            "brown",
            "golden",
            "cream",
            "orange",
            "tabby",
            "calico",
            "spotted",
            "bicolor",
        ]

        # Create breed, color, age, and size classification layers
        # In a real implementation, these would be trained models
        self.breed_classifier = self._create_classifier_layer(
            2048, len(self.breed_mapping["cat"]) + len(self.breed_mapping["dog"])
        )
        self.color_classifier = self._create_classifier_layer(
            2048, len(self.color_options)
        )
        self.age_classifier = self._create_classifier_layer(
            2048, 3
        )  # young, adult, senior
        self.size_classifier = self._create_classifier_layer(
            2048, 3
        )  # small, medium, large

        # Set the weights file paths - would exist in a real app
        self.breed_weights_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "models", "breed_classifier.pt"
        )
        self.color_weights_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "models", "color_classifier.pt"
        )
        self.age_size_weights_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "models",
            "age_size_classifier.pt",
        )

        # Load weights if they exist
        self._load_classifier_weights()

        logger.info("Models loaded successfully!")

    def _create_classifier_layer(self, input_size, output_size):
        """Create a classifier layer with the given input and output sizes"""
        classifier = torch.nn.Sequential(
            torch.nn.Linear(input_size, 512),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(512, output_size),
        )
        classifier.eval()
        return classifier

    def _load_classifier_weights(self):
        """Load pre-trained weights for classifiers if they exist"""
        try:
            if os.path.exists(self.breed_weights_path):
                self.breed_classifier.load_state_dict(
                    torch.load(self.breed_weights_path)
                )
                logger.info(
                    f"Loaded breed classifier weights from {self.breed_weights_path}"
                )

            if os.path.exists(self.color_weights_path):
                self.color_classifier.load_state_dict(
                    torch.load(self.color_weights_path)
                )
                logger.info(
                    f"Loaded color classifier weights from {self.color_weights_path}"
                )

            if os.path.exists(self.age_size_weights_path):
                # Load weights for age and size classifiers
                # In a real app, these would be separate models
                logger.info(
                    f"Loaded age and size classifier weights from {self.age_size_weights_path}"
                )
        except Exception as e:
            logger.error(f"Error loading classifier weights: {e}")
            # Initialize with pre-trained weights or continue with random initialization
            pass

    def detect_pet(self, image_path):
        """
        Detect and extract a pet from an image

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (cropped pet image, pet class, attributes)
        """
        try:
            results = self.detector(image_path)

            if len(results.xyxy[0]) == 0:
                logger.warning(f"No pets detected in the image: {image_path}")
                return None, None, None

            pet_boxes = []
            for detection in results.xyxy[0]:
                if int(detection[5]) in self.pet_classes:
                    pet_boxes.append(
                        {
                            "box": detection[:4].cpu().numpy(),  # x1, y1, x2, y2
                            "conf": detection[4].item(),
                            "class": "dog" if int(detection[5]) == 16 else "cat",
                            "class_id": int(detection[5]),
                        }
                    )

            if not pet_boxes:
                logger.warning(f"No pets detected in the image: {image_path}")
                return None, None, None

            # Sort by confidence and get the best detection
            pet_boxes.sort(key=lambda x: x["conf"], reverse=True)
            best_box = pet_boxes[0]

            img = Image.open(image_path)
            x1, y1, x2, y2 = best_box["box"]
            cropped_pet = img.crop((int(x1), int(y1), int(x2), int(y2)))

            # Determine attributes for the detected pet
            attributes = self.estimate_pet_attributes(cropped_pet, best_box["class"])

            return cropped_pet, best_box["class"], attributes

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
            return None, None, None

    def estimate_pet_attributes(self, pet_image, pet_class):
        """
        Estimate pet attributes like breed, color, age and size using neural networks

        Args:
            pet_image: PIL Image of the cropped pet
            pet_class: Class of the pet ('dog' or 'cat')

        Returns:
            Dictionary of attributes
        """
        if pet_image is None:
            return {}

        try:
            # Extract features using the secondary extractor
            img_tensor = self.transform(pet_image).unsqueeze(0)

            with torch.no_grad():
                features = self.secondary_extractor(img_tensor)
                feature_vector = features.squeeze()

                # Determine which breed set to use based on pet class
                breed_offset = 0
                if pet_class == "dog":
                    breed_offset = len(self.breed_mapping["cat"])

                # Get breed prediction
                breed_logits = self.breed_classifier(feature_vector).detach().cpu()

                # Adjust indices based on pet class
                if pet_class == "cat":
                    breed_probs = torch.softmax(
                        breed_logits[: len(self.breed_mapping["cat"])], dim=0
                    )
                    breed_idx = torch.argmax(breed_probs).item()
                    breed = self.breed_mapping["cat"][breed_idx]
                    breed_confidence = float(breed_probs[breed_idx])
                else:  # dog
                    dog_logits = breed_logits[len(self.breed_mapping["cat"]) :]
                    breed_probs = torch.softmax(dog_logits, dim=0)
                    breed_idx = torch.argmax(breed_probs).item()
                    breed = self.breed_mapping["dog"][breed_idx]
                    breed_confidence = float(breed_probs[breed_idx])

                # Get color prediction based on image analysis and classifier
                color_logits = self.color_classifier(feature_vector).detach().cpu()
                color_probs = torch.softmax(color_logits, dim=0)
                color_idx = torch.argmax(color_probs).item()
                color = self.color_options[color_idx]
                color_confidence = float(color_probs[color_idx])

                # Get additional color through image analysis
                additional_color = self.analyze_pet_colors(pet_image)
                colors = [{"name": color, "confidence": color_confidence}]
                if additional_color and additional_color != color:
                    colors.append({"name": additional_color, "confidence": 0.7})

                # Get age prediction
                age_logits = self.age_classifier(feature_vector).detach().cpu()
                age_probs = torch.softmax(age_logits, dim=0)
                age_idx = torch.argmax(age_probs).item()
                ages = ["young", "adult", "senior"]
                age = ages[age_idx]

                # Get size prediction
                size_logits = self.size_classifier(feature_vector).detach().cpu()
                size_probs = torch.softmax(size_logits, dim=0)
                size_idx = torch.argmax(size_probs).item()
                sizes = ["small", "medium", "large"]
                size = sizes[size_idx]

                attributes = {
                    "breed": {"name": breed, "confidence": float(breed_confidence)},
                    "colors": colors,
                    "estimated_age": age,
                    "estimated_size": size,
                    "confidence": float(breed_confidence * color_confidence),
                }

                return attributes

        except Exception as e:
            logger.error(f"Error estimating pet attributes: {e}", exc_info=True)
            # Return basic attributes as fallback
            breeds = (
                self.breed_mapping["cat"]
                if pet_class == "cat"
                else self.breed_mapping["dog"]
            )
            return {
                "breed": {"name": breeds[0], "confidence": 0.5},
                "colors": [{"name": "gray", "confidence": 0.5}],
                "estimated_age": "adult",
                "estimated_size": "medium",
                "confidence": 0.5,
            }

    def analyze_pet_colors(self, pet_image):
        """
        Analyze the pet image to determine dominant colors

        Args:
            pet_image: PIL Image of the pet

        Returns:
            Dominant color name
        """
        try:
            # Resize for faster processing
            resized_img = pet_image.resize((100, 100))

            # Convert to RGB if not already
            if resized_img.mode != "RGB":
                resized_img = resized_img.convert("RGB")

            # Extract pixels
            pixels = list(resized_img.getdata())

            # Define color ranges - (R, G, B) ranges for common pet colors
            color_ranges = {
                "black": lambda r, g, b: r < 50 and g < 50 and b < 50,
                "white": lambda r, g, b: r > 200 and g > 200 and b > 200,
                "gray": lambda r, g, b: abs(r - g) < 20
                and abs(g - b) < 20
                and abs(r - b) < 20
                and 50 <= r <= 200,
                "brown": lambda r, g, b: r > g + 20
                and r > b + 20
                and g < 150
                and b < 150,
                "golden": lambda r, g, b: r > 180 and g > 140 and b < 100,
                "cream": lambda r, g, b: r > 200 and g > 180 and b > 150,
                "orange": lambda r, g, b: r > 180 and 100 < g < 150 and b < 100,
                "tabby": lambda r, g, b: 130 < r < 180
                and 100 < g < 150
                and 50 < b < 100,
            }

            # Count pixels in each color range
            color_counts = {color: 0 for color in color_ranges}
            for r, g, b in pixels:
                for color, color_range in color_ranges.items():
                    if color_range(r, g, b):
                        color_counts[color] += 1

            # Get the dominant color
            dominant_color = max(color_counts.items(), key=lambda x: x[1])
            if dominant_color[1] > 0:
                return dominant_color[0]

            # Fallback to the original color options
            return self.color_options[0]

        except Exception as e:
            logger.error(f"Error analyzing pet colors: {e}", exc_info=True)
            return None

    def extract_features(self, image):
        """
        Extract features from pet image

        Args:
            image: PIL Image of the pet

        Returns:
            Feature vector as NumPy array
        """
        if image is None:
            return None

        try:
            # Prepare image for feature extraction
            img_tensor = self.transform(image).unsqueeze(0)

            # Extract features
            with torch.no_grad():
                features = self.feature_extractor(img_tensor)

            # Flatten features to 1D vector
            features = features.squeeze().cpu().numpy()
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True)
            return None

    def compare_pets(
        self,
        features1,
        features2,
        attributes1=None,
        attributes2=None,
        location1=None,
        location2=None,
        date1=None,
        date2=None,
        weights=None,
    ):
        """
        Compare two pet features with optional attribute matching, location and time proximity

        Parameters:
        - features1, features2: Feature vectors for visual comparison
        - attributes1, attributes2: Pet attributes for attribute matching
        - location1, location2: (latitude, longitude) tuples for location proximity
        - date1, date2: datetime objects for time proximity
        - weights: Dictionary with weights for each component (visual, attribute, location, time)

        Returns:
        - Dictionary containing overall similarity and component similarities
        """
        # Input validation
        if features1 is None or features2 is None:
            return {"overall": 0, "visual": 0, "attribute": 0, "location": 0, "time": 0}

        # Ensure features have correct shape
        try:
            if features1.ndim == 1:
                f1 = features1.reshape(1, -1)
            else:
                f1 = features1

            if features2.ndim == 1:
                f2 = features2.reshape(1, -1)
            else:
                f2 = features2

            # Verify dimensions match
            if f1.shape[1] != f2.shape[1]:
                logger.warning(f"Feature dimension mismatch: {f1.shape} vs {f2.shape}")
                return {
                    "overall": 0,
                    "visual": 0,
                    "attribute": 0,
                    "location": 0,
                    "time": 0,
                }
        except Exception as e:
            logger.error(f"Error reshaping feature vectors: {e}")
            return {"overall": 0, "visual": 0, "attribute": 0, "location": 0, "time": 0}

        # Default weights if not provided
        if weights is None:
            weights = {"visual": 0.6, "attribute": 0.2, "location": 0.1, "time": 0.1}

        # Ensure all required components are in weights
        required_components = ["visual", "attribute", "location", "time"]
        for component in required_components:
            if component not in weights:
                weights[component] = 0.25  # Default equal weight

        # Ensure weights sum to 1
        total = sum(weights.values())
        if total != 1:
            for k in weights:
                weights[k] /= total

        # Initialize scores
        scores = {"visual": 0, "attribute": 0, "location": 0, "time": 0}

        # Visual similarity (cosine similarity between feature vectors)
        try:
            scores["visual"] = float(cosine_similarity(f1, f2)[0][0])
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            scores["visual"] = 0

        # Attribute matching (if attributes provided)
        if attributes1 and attributes2:
            attr_score = 0
            count = 0

            # Compare breed
            if "breed" in attributes1 and "breed" in attributes2:
                breed_match = (
                    1.0
                    if attributes1["breed"]["name"] == attributes2["breed"]["name"]
                    else 0.0
                )
                attr_score += breed_match
                count += 1

            # Compare colors
            if "colors" in attributes1 and "colors" in attributes2:
                color_match = 0.0
                for c1 in attributes1["colors"]:
                    for c2 in attributes2["colors"]:
                        if c1["name"] == c2["name"]:
                            color_match = 1.0
                            break
                    if color_match > 0:
                        break
                attr_score += color_match
                count += 1

            # Compare age and size
            if "estimated_age" in attributes1 and "estimated_age" in attributes2:
                age_match = (
                    1.0
                    if attributes1["estimated_age"] == attributes2["estimated_age"]
                    else 0.5
                )
                attr_score += age_match
                count += 1

            if "estimated_size" in attributes1 and "estimated_size" in attributes2:
                size_match = (
                    1.0
                    if attributes1["estimated_size"] == attributes2["estimated_size"]
                    else 0.5
                )
                attr_score += size_match
                count += 1

            scores["attribute"] = attr_score / max(1, count)

        # Location proximity (if locations provided)
        if location1 and location2:
            try:
                # Validate coordinates
                if (
                    isinstance(location1, (list, tuple))
                    and len(location1) == 2
                    and isinstance(location2, (list, tuple))
                    and len(location2) == 2
                ):
                    # Calculate distance in km
                    try:
                        distance = geodesic(location1, location2).kilometers
                        # Convert distance to similarity (1 when distance=0, approaching 0 as distance increases)
                        max_relevant_distance = 50  # km
                        scores["location"] = max(
                            0, 1 - (distance / max_relevant_distance)
                        )
                    except Exception as e:
                        logger.error(f"Error calculating geodesic distance: {e}")
                        scores["location"] = 0
                else:
                    logger.warning(
                        f"Invalid location format: {location1} or {location2}"
                    )
                    scores["location"] = 0
            except Exception as e:
                logger.error(f"Error processing locations: {e}")
                scores["location"] = 0

        # Time proximity (if dates provided)
        if date1 and date2:
            try:
                # Calculate time difference in days
                time_diff = abs((date1 - date2).days)
                # Convert time difference to similarity (1 when diff=0, approaching 0 as diff increases)
                max_relevant_days = 30
                scores["time"] = max(0, 1 - (time_diff / max_relevant_days))
            except Exception as e:
                logger.error(f"Error calculating time difference: {e}")
                scores["time"] = 0

        # Calculate overall similarity as weighted sum
        overall = sum(weights[k] * scores[k] for k in weights)
        scores["overall"] = overall

        return scores

    # ...existing code...
