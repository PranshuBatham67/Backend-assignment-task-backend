from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from app.core.exceptions import ResourceAlreadyExistsException, ResourceNotFoundException
from typing import Optional, List

class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(
        db: Session, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        """
        Create a new user with hashed password.
        Automatically assigns USER role.
        """
        # Check if user already exists
        existing_user = UserService.get_by_email(db, email)
        if existing_user:
            raise ResourceAlreadyExistsException("User with this email")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser,
            is_active=True
        )
        
        # Assign default USER role
        user_role = db.query(Role).filter(Role.name == "USER").first()
        if not user_role:
            # Create USER role if it doesn't exist
            user_role = Role(name="USER", description="Regular user")
            db.add(user_role)
            db.flush()
        
        user.roles.append(user_role)
        
        # If superuser, also add ADMIN role
        if is_superuser:
            admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
            if not admin_role:
                admin_role = Role(name="ADMIN", description="Administrator")
                db.add(admin_role)
                db.flush()
            user.roles.append(admin_role)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> User:
        """Update user fields"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFoundException("User")
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> User:
        """Deactivate a user account"""
        return UserService.update_user(db, user_id, is_active=False)
