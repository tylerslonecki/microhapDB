# MicrohapDB (HaploSearch)

A comprehensive web application for managing and analyzing microhaplotype genetic data, designed for researchers and institutions working with population genetics and genomic analysis.

## 🧬 What is MicrohapDB?

MicrohapDB is a specialized database system for storing, managing, and analyzing **microhaplotypes** - short DNA sequences that contain multiple closely linked polymorphic sites. These genetic markers are valuable for:

- **Population genetics studies**
- **Ancestry inference**
- **Forensic genetics**
- **Evolutionary research**
- **Biogeographical analysis**

## 🏗️ Architecture Overview

### 🌐 Frontend (Vue.js)
**Location**: `microhapDB-frontend/`

A modern, responsive web interface built with Vue.js that provides:

- **Data Upload & Management**: Upload PAV (Presence/Absence Variation) and MADC (Microhaplotype Allele Data Collection) files
- **Interactive Visualizations**: Charts and graphs for genetic data analysis
- **User Authentication**: ORCID-based login system for researchers
- **Admin Dashboard**: Administrative tools for data management
- **Search & Filter**: Advanced search capabilities across genetic datasets

**Key Features**:
- Real-time data validation during upload
- Batch processing for large datasets
- Export functionality for analysis results
- Role-based access control (Admin/User)
- Integration with ORCID for researcher authentication

### 🔧 Backend (FastAPI)
**Location**: `microhapDB-backend/`

A robust REST API built with FastAPI and Python that handles:

- **Database Management**: PostgreSQL database with optimized schemas
- **File Processing**: Handles PAV and MADC file formats with validation
- **Authentication**: ORCID OAuth integration
- **Data Analysis**: Statistical computations and genetic analysis algorithms
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Performance**: Optimized queries and caching for large datasets

**Key Features**:
- RESTful API with comprehensive endpoints
- Database migrations with Alembic
- Background task processing
- Data validation and error handling
- Comprehensive logging and monitoring
- Docker containerization for deployment

## 🚀 Deployment Architecture

### Production Infrastructure
- **Backend**: AWS EC2 instance with Docker containers
- **Frontend**: AWS S3 + CloudFront for global CDN
- **Database**: PostgreSQL (configurable for AWS RDS)
- **CI/CD**: GitHub Actions for automated deployment
- **Infrastructure**: Terraform for Infrastructure as Code

### Supported Deployment Methods
1. **GitHub Actions** (Recommended): Automated CI/CD pipeline
2. **Terraform**: Infrastructure as Code management
3. **Manual EC2**: Direct deployment to AWS EC2 instances

## 📊 Data Types Supported

### PAV Files (Presence/Absence Variation)
- Binary genetic variation data
- Population frequency information
- Geographic metadata

### MADC Files (Microhaplotype Allele Data Collection)
- Detailed allele frequency data
- Multi-population comparisons
- Statistical analysis results

## 🔐 Security Features

- **ORCID Authentication**: Secure researcher authentication
- **Role-based Access**: Admin and user permission levels
- **Data Validation**: Comprehensive input validation and sanitization
- **Secure File Upload**: Validated file processing with size limits
- **Environment Variables**: Secure configuration management

## 🛠️ Technology Stack

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vue Router**: Client-side routing
- **Axios**: HTTP client for API communication
- **Chart.js**: Data visualization
- **Bootstrap/CSS**: Responsive styling

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **PostgreSQL**: Primary database
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### DevOps & Deployment
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **Terraform**: Infrastructure as Code
- **AWS**: Cloud infrastructure (EC2, S3, CloudFront)
- **Nginx**: Reverse proxy (in production)

## 📈 Use Cases

### For Researchers
- Upload and manage genetic datasets
- Perform population genetics analysis
- Visualize allele frequencies and distributions
- Export data for further analysis
- Collaborate with other researchers

### For Institutions
- Centralized genetic data repository
- Multi-user access with role management
- Standardized data formats and validation
- Scalable infrastructure for large datasets
- Integration with existing research workflows

## 🌍 Target Audience

- **Population Geneticists**: Researchers studying genetic variation in populations
- **Forensic Scientists**: Professionals using genetic markers for identification
- **Evolutionary Biologists**: Scientists studying genetic evolution and ancestry
- **Academic Institutions**: Universities and research centers
- **Government Agencies**: Organizations involved in genetic research and policy

## 📚 Getting Started

### For Users
1. Visit the deployed application
2. Sign in with your ORCID account
3. Upload your genetic data files (PAV/MADC format)
4. Explore visualizations and analysis tools
5. Export results for your research

### For Developers
1. Clone the repository
2. Set up the backend (see `microhapDB-backend/README.md`)
3. Set up the frontend (see `microhapDB-frontend/README.md`)
4. Configure environment variables
5. Run locally for development

## 🤝 Contributing

We welcome contributions from the genetics and bioinformatics community! Please see our contributing guidelines and feel free to submit issues or pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Live Application**: [Deployed URL]
- **API Documentation**: [Backend URL]/docs
- **GitHub Repository**: https://github.com/tylerslonecki/microhapDB
- **Issues & Support**: [GitHub Issues](https://github.com/tylerslonecki/microhapDB/issues)

---

*MicrohapDB is developed to support the global genetics research community in advancing our understanding of human genetic diversity and evolution.* 

