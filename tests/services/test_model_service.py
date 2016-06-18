# external imports
import unittest
# local imports
import nautilus
from nautilus import conventions
from nautilus.conventions import services as service_conventions
import nautilus.models as models
import nautilus.network.events.actionHandlers as action_handlers
from ..util import async_test, Mock

class TestUtil(unittest.TestCase):

    def setUp(self):
        # point the database to a in-memory sqlite database
        nautilus.database.init_db('sqlite:///test.db')

        # create a spy we can check for later
        self.spy = Mock()

        class TestModelService(nautilus.models.BaseModel):
            name = nautilus.models.fields.CharField()

        class TestService(nautilus.ModelService):
            model = TestModelService
            additional_action_handler = self.spy

        # save the class records to the suite
        self.model = TestModelService
        self.service = TestService()
        self.action_handler = self.service.action_handler()
        self.service_record = TestService

        # create the test table
        self.model.create_table(True)


    def tearDown(self):
        self.model.drop_table()


    def test_must_provide_a_model(self):
        # this should throw an exception
        def test_empty_class():
            class TestModel(nautilus.ModelService): pass
            # instantiate the incorrect service
            TestModel()

        # expect an error
        self.assertRaises(ValueError, test_empty_class)


    def test_has_conventional_name(self):
        assert self.service_record.name == \
                    service_conventions.model_service_name(self.model), (
            "Model service did not have the correct name."
        )


    def test_has_valid_schema(self):
        assert hasattr(self.service, 'schema') and self.service.schema, (
            "Model Service did not have a schema."
        )

        # the query to test the schema
        query = """
            query {
                all_models {
                    name
                }
            }
        """

        parsed_query = self.service.schema.execute(query)

        # make sure there are no errors
        assert parsed_query.errors == [], (
            "Model service schema is invalid."
        )
        assert len(parsed_query.data) > 0, (
            "Model could not be retrieved with schema."
        )

    @async_test
    async def test_can_provide_addtnl_action_handler(self):
        # make sure there is a handler to call
        assert hasattr(self.service, 'action_handler'), (
            "Test Service does not have an action handler"
        )
        # values to test against
        action_type = 'asdf'
        payload = 'asdf'

        # call the service action handler
        await self.action_handler.handle_action(
            action_type,
            payload
        )

        # make sure the spy was called correctly
        self.spy.assert_called(
            action_type,
            payload
        )

    @async_test
    async def test_action_handler_supports_crud(self):
        await self._verify_create_action_handler()
        await self._verify_update_action_handler()
        await self._verify_delete_action_handler()


    async def _verify_create_action_handler(self):
        # fire a create action
        await self.action_handler.handle_action(
            conventions.get_crud_action('create', self.model),
            dict(name='foo'),
        )
        # make sure the created record was found and save the id
        self.model_id = self.model.get(self.model.name == 'foo').id


    async def _verify_update_action_handler(self):
        # fire an update action
        await self.action_handler.handle_action(
            conventions.get_crud_action('update', self.model),
            dict(id=self.model_id, name='barz'),
        )
        # check that a model matches
        self.model.get(self.model.name == 'barz')


    async def _verify_delete_action_handler(self):
        # fire a delete action
        await self.action_handler.handle_action(
            conventions.get_crud_action('delete', self.model),
            payload=self.model_id
        )
        # expect an error
        self.assertRaises(Exception, self.model.get, self.model_id)
