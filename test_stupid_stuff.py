from iris.server.models import User
u = User(name="david", language="en", password="testing", role="admin")
u.save_to_file()
