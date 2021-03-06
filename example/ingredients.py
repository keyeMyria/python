"""
    This service maintains the list of ingredients in our cloud.
"""

# third party imports
from nautilus import ModelService
# third party imports
from nautilus.models import BaseModel, fields

class Ingredient(BaseModel):
    name = fields.CharField()

class ServiceConfig:
    database_url = 'sqlite:///ingredients.db'

class IngredientService(ModelService):
    model = Ingredient,
    config = ServiceConfig

# create a service manager to run the service
manager = ServiceManager(IngredientService)

if __name__ == '__main__':
    manager.run()
