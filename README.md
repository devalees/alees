# Alees ERP System

A modern, cloud-based Enterprise Resource Planning (ERP) system built with Django and Next.js.

## Project Overview

This project implements a comprehensive ERP system with the following key features:

- Modern API-first architecture
- Test-Driven Development (TDD) approach
- Microservices-based design
- Real-time capabilities
- Comprehensive project management features
- Client portal integration
- Document management system

## Technology Stack

### Backend
- Django & Django REST Framework
- PostgreSQL
- Celery with Redis
- Elasticsearch/OpenSearch
- Django Channels for WebSocket support

### Frontend
- Next.js
- React
- TypeScript

### Testing
- Pytest
- Factory Boy
- Coverage

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/devalees/alees.git
cd alees
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements/base.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Testing

Run the test suite:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
