#!/bin/bash

# Create base file with header
echo "# Infrastructure Strategy" > docs/architecture/merged_infrastructure_strategy.md
echo "" >> docs/architecture/merged_infrastructure_strategy.md
echo "## Table of Contents" >> docs/architecture/merged_infrastructure_strategy.md
echo "" >> docs/architecture/merged_infrastructure_strategy.md

# Add table of contents
cat << 'EOF' >> docs/architecture/merged_infrastructure_strategy.md
1. [Database Management](#database-management)
   - [PostgreSQL](#postgresql)
   - [Migration Strategy](#migration-strategy)

2. [Caching & Storage](#caching--storage)
   - [Redis Caching](#redis-caching)
   - [File Storage](#file-storage)

3. [Asynchronous Processing](#asynchronous-processing)
   - [Celery Tasks](#celery-tasks)

---
EOF

# Database Management
echo -e "\n## Database Management\n" >> docs/architecture/merged_infrastructure_strategy.md
echo -e "\n### PostgreSQL\n" >> docs/architecture/merged_infrastructure_strategy.md
cat docs/architecture/infrastrcture/database_postgresql.md >> docs/architecture/merged_infrastructure_strategy.md
echo -e "\n### Migration Strategy\n" >> docs/architecture/merged_infrastructure_strategy.md
cat docs/architecture/infrastrcture/migration_and_db_management_strategy.md >> docs/architecture/merged_infrastructure_strategy.md

# Caching & Storage
echo -e "\n## Caching & Storage\n" >> docs/architecture/merged_infrastructure_strategy.md
echo -e "\n### Redis Caching\n" >> docs/architecture/merged_infrastructure_strategy.md
cat docs/architecture/infrastrcture/cache_redis.md >> docs/architecture/merged_infrastructure_strategy.md
echo -e "\n### File Storage\n" >> docs/architecture/merged_infrastructure_strategy.md
cat docs/architecture/infrastrcture/file_storage.md >> docs/architecture/merged_infrastructure_strategy.md

# Asynchronous Processing
echo -e "\n## Asynchronous Processing\n" >> docs/architecture/merged_infrastructure_strategy.md
echo -e "\n### Celery Tasks\n" >> docs/architecture/merged_infrastructure_strategy.md
cat docs/architecture/infrastrcture/asynchronous_celery.md >> docs/architecture/merged_infrastructure_strategy.md 