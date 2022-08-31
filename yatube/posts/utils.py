from django.contrib.auth.mixins import UserPassesTestMixin


class AuthorUserPassesTestMixin(UserPassesTestMixin):

    def test_func(self):
        self.object = self.get_object()
        return self.request.user == self.object.author
