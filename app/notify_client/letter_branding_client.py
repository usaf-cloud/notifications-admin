from app.notify_client import NotifyAdminAPIClient


class LetterBrandingClient(NotifyAdminAPIClient):

    def __init__(self):
        super().__init__("a" * 73, "b")

    def get_all_letter_brandings(self):
        return self.get(url='/dvla_organisations')
