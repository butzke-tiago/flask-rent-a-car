from .category import service as category_service, DuplicateCategoryError
from .make import service as make_service, DuplicateMakeError
from .model import service as model_service, DuplicateModelError
from .store import service as store_service, DuplicateStoreError
from .tag import service as tag_service, DuplicateTagError
from .user import service as user_service, DuplicateUserError
from .vehicle import service as vehicle_service, DuplicateVehicleError
