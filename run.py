import os
import sys
import logging
import uvicorn
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run")


def main():
    # Get port from environment or use default
    try:
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Using PORT: {port}")
    except ValueError:
        logger.error(
            f"Invalid PORT value: {os.environ.get('PORT')}, using default 8000"
        )
        port = 8000

    # Run database migrations if alembic is available
    try:
        logger.info("Attempting to run database migrations...")
        subprocess.run(["alembic", "upgrade", "head"], check=False)
    except Exception as e:
        logger.warning(f"Could not run migrations: {str(e)}")

    # Start the application
    logger.info(f"Starting application on port {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
