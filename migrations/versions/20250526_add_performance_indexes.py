"""
Add performance indexes to the database.

This migration adds optimized indexes for frequently queried columns to
improve API performance following the SurgeonMatch Project Standards.
"""
import sqlalchemy as sa
from alembic import op


# Revision identifiers
revision = '20250526_add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes."""
    # Surgeons table indexes
    op.create_index(
        op.f('ix_surgeons_specialty'), 
        'surgeons', 
        ['specialty'], 
        unique=False
    )
    op.create_index(
        op.f('ix_surgeons_location'), 
        'surgeons', 
        ['latitude', 'longitude'], 
        unique=False
    )
    op.create_index(
        op.f('ix_surgeons_city_state'), 
        'surgeons', 
        ['city', 'state'], 
        unique=False
    )
    
    # Claims table indexes
    op.create_index(
        op.f('ix_claims_procedure_code'), 
        'claims', 
        ['procedure_code'], 
        unique=False
    )
    op.create_index(
        op.f('ix_claims_date'), 
        'claims', 
        ['date'], 
        unique=False
    )
    op.create_index(
        op.f('ix_claims_total_cost'), 
        'claims', 
        ['total_cost'], 
        unique=False
    )
    
    # Quality metrics indexes
    op.create_index(
        op.f('ix_quality_metrics_metric_name_value'), 
        'quality_metrics', 
        ['metric_name', 'metric_value'], 
        unique=False
    )
    op.create_index(
        op.f('ix_quality_metrics_date'), 
        'quality_metrics', 
        ['date'], 
        unique=False
    )
    
    # Rate limiting table index
    op.create_index(
        op.f('ix_rate_limits_last_request'), 
        'rate_limits', 
        ['last_request'], 
        unique=False
    )


def downgrade():
    """Remove performance indexes."""
    # Surgeons table indexes
    op.drop_index(op.f('ix_surgeons_specialty'), table_name='surgeons')
    op.drop_index(op.f('ix_surgeons_location'), table_name='surgeons')
    op.drop_index(op.f('ix_surgeons_city_state'), table_name='surgeons')
    
    # Claims table indexes
    op.drop_index(op.f('ix_claims_procedure_code'), table_name='claims')
    op.drop_index(op.f('ix_claims_date'), table_name='claims')
    op.drop_index(op.f('ix_claims_total_cost'), table_name='claims')
    
    # Quality metrics indexes
    op.drop_index(op.f('ix_quality_metrics_metric_name_value'), table_name='quality_metrics')
    op.drop_index(op.f('ix_quality_metrics_date'), table_name='quality_metrics')
    
    # Rate limiting table index
    op.drop_index(op.f('ix_rate_limits_last_request'), table_name='rate_limits')
