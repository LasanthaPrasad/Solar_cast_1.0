from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_mail import Mail

db = SQLAlchemy()
security = Security()
mail = Mail()

# Remove these lines
# sqlalchm = SQLAlchemyUserDatastore()
# customuserdatastore = CustomUserDatastore(sqlalchm)

# We'll initialize user_datastore in create_app function

class CustomUserDatastore(SQLAlchemyUserDatastore):
    def confirm_user(self, user):
        """Confirms a user, activates them and assigns the 'user' role."""
        super().confirm_user(user)  # Call the parent method
        user.active = True
        user_role = self.find_role('user')
        if user_role and user_role not in user.roles:
            user.roles.append(user_role)
        self.put(user)
        return user

# We'll create an instance of CustomUserDatastore in create_app function