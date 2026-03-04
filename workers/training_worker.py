from core.logging import logger
from infrastructure.database.repository import ListingRepository
from infrastructure.database.session import async_session
from ml.feature_engineering.feature_builder import FeatureBuilder
from ml.models.demand_model import DemandModel
from ml.models.price_model import PriceModel
from ml.models.similarity_model import SimilarityModel


class TrainingWorker:
    def __init__(self):
        self.feature_builder = FeatureBuilder()
        self.similarity_model = SimilarityModel()
        self.demand_model = DemandModel()
        self.price_model = PriceModel()

    async def run(self) -> None:
        logger.info("Starting training worker")

        async with async_session() as session:
            listing_repo = ListingRepository(session)
            listings = await listing_repo.get_all()

            if not listings:
                logger.warning("No listings found, skipping training")
                return

            await self._train_similarity(listings)

        logger.info("Training worker completed")

    async def _train_similarity(self, listings) -> None:
        features = self.feature_builder.build_batch_features(listings)
        listing_ids = [l.id for l in listings]

        self.similarity_model.fit(features, listing_ids)
        self.similarity_model.save()

        logger.info("Similarity model trained with %d listings", len(listings))
