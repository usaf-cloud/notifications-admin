from app.notify_client import NotifyAdminAPIClient


class LetterBrandingClient(NotifyAdminAPIClient):

    def __init__(self):
        super().__init__("a" * 73, "b")

    def get_all_letter_brandings(self):
        return self.get(url='/dvla_organisations')

    def get_letter_branding(self, dvla_org_id):
        return self.get(url='/dvla_organisations/{}'.format(dvla_org_id))
