
def test_get_dashboard_partials():
    # test big blue numbers
    # json method that returns dict --> can I test that directly

    # mocks: template_statistics_client.get_template_statistics_for_service
    #

@fixture
def get_template_stats(...):
    yield mock

    assert mock.called

@fixture
def patch(mocker):
    def f(method_name, return_value=None):
        if return_value is None:
            return_value = getattr(module, '_{}'.format(method_name))
        mock = yield mocker.patch('app.{}'.format(method_name), autospec=True, return_value=_)
        assert mock.called


# def test_dashboard_with_fixture_mocks(
#         get_template_stats,
#         get_scheduled_jobs,
#         get_immediate_jobs,
#         has_jobs,
# ):
#     get_template_stats.return_value = {...}
#     get_scheduled_jobs.return_value = _scheduled_jobs(...)
#
#     get_scheduled_jobs.set_return_value(name=..., notifications=[_notification(name=...)])
#
#     get_template_stats.assert_called_once_with(...)

def _get_template(has_placeholders=True)


@logged_in_as(fakes.user(platform_admin=True))
def test_dashboard_with_in_test_mocks(patch, user):
    patch('service_api_client.get_service')
    patch('user_api_client.get_user', user)

    patch('get_template', fakes.get_template(content='blah {{thing}}'))
    patch('template_api_client.get_template', fakes.get_template(has_placeholders=True))

    template_stats = patch('service_api_client.get_template_stats', fakes.get_template_stats(...))
    scheduled_jobs = patch('get_scheduled_jobs', fakes.get_scheduled_jobs(name=..., notifications=[fakes.notification(name=...)]))

    client_request.get('.blahblahblah')

    template_stats.assert_called_once_with(...)



#
# def test_dashboard_with_client_mock():
#     api_client.service_id = 'awdaw'
#     api_client.scheduled_jobs['notifications'] = [api_client._notification(name=...)]
#
#     api_client.patch()
#
#
#
# class ApiClient():
#     def __init__(**kwargs):
#         self.service_id = kwargs.get('service_id', SERVICE_ONE)
#         ...
#
#     def patch(self):
#         mocker.patch('app.service_api_client.get_service', return_value=self.something, autospec=True)
#         mocker.patch('app.template_api_client', return_value=self.template_something, autospec=True)
#
#
#     def something(self):
#         return {
#             'service_id': self.service_id,
#             'templates': [
#                 self.template(name='...')
#             ]
#         }
#
#     def template(self, name):
#         return {
#             'name': name,
#             'service_id': self.service_id
#         }