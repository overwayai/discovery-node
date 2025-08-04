# Reduced Memory Deployment Configuration

This document describes the changes made to reduce memory usage for deployment on Render with 512MB memory limit.

## Disabled Tasks

The following Celery tasks have been disabled to reduce memory footprint:

### 1. Ingestion Tasks (commented out in celery_app.py)
- `ingest:all` - Full ingestion pipeline
- `ingest:feed` - Product feed ingestion  
- `ingest:registry` - Brand registry ingestion
- `ingest:vector` - Vector embedding generation for bulk data
- `ingest:schedule_all` - Schedule all ingestion tasks
- `ingest:check_feed_updates` - Periodic feed update checks

### 2. Cleanup Tasks (commented out in celery_app.py)
- `cleanup:old_products` - Remove old deleted products
- `cleanup:orphaned_data` - Clean up orphaned database records
- `cleanup:celery_tasks` - Clean up old Celery task results

## Active Tasks

Only embedding generation tasks remain active:
- `embeddings:generate_single` - Generate embeddings for single products (via admin API)
- `embeddings:generate_batch` - Generate embeddings for batches of products (via admin API)
- `embeddings:regenerate_organization` - Bulk regenerate embeddings for an organization

## Worker Configuration

The Celery worker now runs with:
```bash
celery -A app.worker.celery_app worker --loglevel=info -Q celery,embeddings_high,embeddings_bulk --without-heartbeat --without-gossip --without-mingle
```

Optimization flags:
- `--without-heartbeat` - Disables heartbeat events
- `--without-gossip` - Disables worker gossip 
- `--without-mingle` - Disables worker synchronization on startup

## How to Run Ingestion Manually

Since automatic ingestion is disabled, run it manually when needed:

```bash
# Via CLI
python main.py ingest --ingestor <ingestor-name> --type all

# Via API endpoint (if implemented)
POST /api/admin/trigger-ingestion
```

## Re-enabling Tasks

To re-enable tasks when more memory is available:

1. Uncomment the task modules in `app/worker/celery_app.py`:
   ```python
   include=[
       "app.worker.tasks.ingest",  # Uncomment this
       "app.worker.tasks.cleanup",  # Uncomment this
       "app.worker.tasks.embeddings",
   ],
   ```

2. Uncomment the task routes:
   ```python
   task_routes={
       # ... embedding routes ...
       "ingest:*": {"queue": "celery"},  # Uncomment this
       "cleanup:*": {"queue": "celery"},  # Uncomment this
   },
   ```

3. Re-enable scheduled tasks in `app/worker/schedulers.py`

4. Re-enable the worker_ready hook in `app/worker/celery_app.py`

## Memory Optimization Tips

If still experiencing memory issues:

1. Add concurrency limit: `--concurrency=1`
2. Set max memory per child: `--max-memory-per-child=400000` (400MB)
3. Run separate workers for different task types
4. Consider upgrading to a larger Render plan

## Production Recommendations

For production deployments:
- Use at least 1GB RAM for the worker
- Run separate workers for ingestion and embeddings
- Enable monitoring to track memory usage
- Set up alerts for OOM errors