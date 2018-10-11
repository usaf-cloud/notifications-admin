from app.notify_client.letter_branding_client import LetterBrandingClient


def test_get_all_letter_brandings(mocker):
    mock_get = mocker.patch('app.notify_client.letter_branding_client.LetterBrandingClient.get')
    LetterBrandingClient().get_all_letter_brandings()
    mock_get.assert_called_once_with(
        url='/dvla_organisations'
    )
