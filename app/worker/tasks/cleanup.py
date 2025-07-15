# app/worker/tasks/cleanup.py
"""
Celery tasks for maintenance and cleanup operations.
"""
import logging
from datetime import datetime, timedelta
from celery import shared_task
from app.db.base import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

@shared_task(name="cleanup:old_products")
def cleanup_old_products():
    """
    Clean up products that have been marked as deleted for a certain period.
    """
    try:
        logger.info("Starting cleanup of old deleted products")
        
        # Create session
        db_session = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from sqlalchemy import text
            
            # Set retention period (default: 30 days)
            retention_days = settings.DELETED_PRODUCT_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old products
            result = db_session.execute(
                text("DELETE FROM products WHERE deleted_at IS NOT NULL AND deleted_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            
            logger.info(f"Deleted {deleted_count} old products")
            db_session.commit()
            
            return {"status": "success", "deleted_count": deleted_count}
        finally:
            db_session.close()
    except Exception as e:
        logger.exception(f"Error cleaning up old products: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(name="cleanup:orphaned_data")
def cleanup_orphaned_data():
    """
    Clean up orphaned data such as categories without products.
    """
    try:
        logger.info("Starting cleanup of orphaned data")
        
        # Create session
        db_session = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from sqlalchemy import text
            
            # Delete category associations for non-existent products
            result1 = db_session.execute(
                text("""
                    DELETE FROM product_category 
                    WHERE product_id NOT IN (SELECT id FROM products)
                """)
            )
            
            # Delete category associations for non-existent categories
            result2 = db_session.execute(
                text("""
                    DELETE FROM product_category 
                    WHERE category_id NOT IN (SELECT id FROM categories)
                """)
            )
            
            # Delete empty categories (optional, depending on business rules)
            if settings.DELETE_EMPTY_CATEGORIES:
                result3 = db_session.execute(
                    text("""
                        DELETE FROM categories 
                        WHERE id NOT IN (
                            SELECT category_id FROM product_category
                            UNION
                            SELECT category_id FROM organization_category
                            UNION
                            SELECT category_id FROM brand_category
                        )
                    """)
                )
                deleted_categories = result3.rowcount
            else:
                deleted_categories = 0
            
            db_session.commit()
            
            return {
                "status": "success", 
                "deleted_product_category_assocs": result1.rowcount + result2.rowcount,
                "deleted_categories": deleted_categories
            }
        finally:
            db_session.close()
    except Exception as e:
        logger.exception(f"Error cleaning up orphaned data: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task(name="cleanup:celery_tasks")
def cleanup_celery_tasks():
    """
    Clean up old Celery task results to prevent database bloat.
    """
    try:
        logger.info("Starting cleanup of old Celery task results")
        
        # This assumes you're using a database backend for Celery results
        # Adjust as needed if using Redis or other backends
        
        # Create session
        db_session = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from sqlalchemy import text
            
            # Set retention period (default: 7 days)
            retention_days = settings.CELERY_RESULT_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old task results
            result = db_session.execute(
                text("DELETE FROM celery_taskmeta WHERE date_done < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            
            logger.info(f"Deleted {deleted_count} old Celery task results")
            db_session.commit()
            
            return {"status": "success", "deleted_count": deleted_count}
        finally:
            db_session.close()
    except Exception as e:
        logger.exception(f"Error cleaning up Celery tasks: {str(e)}")
        return {"status": "error", "message": str(e)}