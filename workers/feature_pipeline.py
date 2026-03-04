from core.logging import logger
from infrastructure.database.session import async_session
from infrastructure.database.repository import ListingRepository
from ml.feature_engineering.feature_builder import FeatureBuilder


class FeaturePipeline:
    def __init__(self):
        self.feature_builder = FeatureBuilder()

    async def run(self) -> None:
        logger.info("Starting feature pipeline")

        async with async_session() as session:
            listing_repo = ListingRepository(session)
            listings = await listing_repo.get_all()

            if not listings:
                logger.warning("No listings found, skipping feature pipeline")
                return

            features = self.feature_builder.build_batch_features(listings)
            logger.info("Built feature matrix: shape %s", features.shape)

            # Store features for downstream model training
            # Features are passed directly to training worker

        logger.info("Feature pipeline completed")
