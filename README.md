# Quiz Platform

The goal of the system is to simulate the core functionalities of an online quiz platform, including user management, quiz creation, real-time communication, asynchronous processing, reporting, and security-focused service communication.

## Table of Contents

* [Key Features](#key-features)
* [Tech Stack](#tech-stack)
* [Roles & Permissions](#roles--permissions)
* [Security Hardening](#security-hardening)
* [Requirements](#requirements)
* [First-time Setup](#first-time-setup)
* [Running the Project](#running-the-project)
* [Database Access](#database-access)
* [Stopping / Starting / Cleaning Up](#stopping--starting--cleaning-up)
* [Deployment](#deployment)
* [License](#license)

## Key Features

* Cookie-based JWT authentication with role-based access control
* User roles: Player, Moderator, Administrator
* Quiz creation, approval, and asynchronous evaluation
* Real-time notifications via WebSockets
* Quiz rankings and result tracking
* PDF report generation and email delivery
* Privacy-focused user data export and account erasure support
* Security-hardened service-to-service communication

## Tech Stack

* Frontend: React with Vite
* Backend: Flask with Python
* Databases: MySQL
* Cache / Token Revocation: Redis
* Communication: REST + WebSockets
* Containerization: Docker & Docker Compose

## Roles & Permissions

### Player

* Registers and logs into the platform
* Browses and plays available quizzes
* Submits quiz answers within the given time limit
* Views personal quiz results and rankings
* Updates personal profile information
* Can export personal data
* Can request account erasure

### Moderator

* Has all Player permissions
* Creates new quizzes with questions, answers, scoring, and duration
* Edits or deletes their own quizzes
* Submits quizzes for administrator approval
* Receives feedback if a quiz is rejected and updates it accordingly

### Administrator

* Has full system access
* Approves or rejects newly created quizzes with a rejection reason
* Manages user accounts
* Changes user roles
* Deletes user accounts
* Generates PDF reports with quiz results
* Receives real-time notifications about newly submitted quizzes

## Security Hardening

This project includes a dedicated security hardening pass focused on authentication, authorization, privacy, API protection, and safer backend communication.

### Implemented Security Improvements

* Added internal service authentication between the main server and `quizService`.
* Added trusted internal identity forwarding using authenticated user ID and role headers.
* Added ownership checks to prevent users from accessing or modifying resources that do not belong to them.
* Added role-based authorization for protected routes.
* Secured WebSocket connections with short-lived authentication tokens and room-level authorization.
* Moved JWT handling from browser storage to HttpOnly cookies.
* Added CSRF protection for cookie-based authentication.
* Added Redis-backed JWT revocation for logout and security-sensitive account changes.
* Added rate limiting for authentication endpoints.
* Added production security headers and Content Security Policy configuration.
* Restricted CORS configuration to explicit frontend origins.
* Added stronger password validation rules.
* Removed unnecessary public exposure of internal services and database ports.
* Added least-privilege database users for application access.
* Added server-side sanitization for quiz content.
* Added safer profile image upload handling through file validation and image re-encoding.
* Reduced unnecessary personal data collection during registration.
* Added privacy-policy consent tracking.
* Added user data export support.
* Added account erasure/anonymization support.
* Added quiz attempt retention cleanup.
* Reduced unnecessary PII transfer between services during report generation.
* Added admin user pagination to avoid unbounded user listing.

### Security Testing

The project also includes security-focused tests covering:

* Internal service authentication
* Quiz execution ownership checks
* Quiz content sanitization
* Role-based authorization
* JWT revocation and logout behavior
* Cookie and CSRF protection
* WebSocket authorization
* Rate limiting
* Report PII minimization
* Admin pagination behavior

## Requirements

* Docker
* Docker Compose
* Python 3.9+ only if running scripts or tests locally
* Linux users: make sure the Docker daemon is running and that your user has permission to run Docker commands. `sudo` may be required depending on your setup.

## First-time Setup

Clone the repository:

```bash
git clone <repo_url>
cd <repo_folder>
```

Create local environment files from the provided examples:

```bash
cp server/.env.example server/.env
cp quizService/.env.example quizService/.env
```

Update the local `.env` files with your own development secrets.

Important: `.env` files must not be committed to Git.

Make scripts executable on Linux/macOS if needed:

```bash
chmod +x wait_for_db.sh
```

Build and start the containers:

```bash
docker compose up --build
```

Or run the containers in the background:

```bash
docker compose up -d --build
```

## Running the Project

Check running containers:

```bash
docker compose ps
```

All required services should be in the `Up` state.

View logs for all containers:

```bash
docker compose logs -f
```

View logs for a specific container:

```bash
docker compose logs -f <container_name>
```

## Database Access

For security reasons, database containers are intended to be accessed from inside the Docker network instead of being publicly exposed through host port mappings.

To inspect the users database from the terminal:

```bash
docker exec -it <users_db_container_name> mysql -u <app_user> -p <database_name>
```

To inspect the quiz database from the terminal:

```bash
docker exec -it <quiz_db_container_name> mysql -u <quiz_app_user> -p <database_name>
```

Use the database usernames, passwords, and database names from your local `.env` files or Docker Compose configuration.

Example:

```bash
docker exec -it users_db mysql -u app_user -p quiz_users_db
```

Inside Docker, services communicate using Docker service names, not `localhost`.

## Stopping / Starting / Cleaning Up

Stop containers:

```bash
docker compose down
```

Start containers again:

```bash
docker compose up -d
```

Rebuild containers:

```bash
docker compose up -d --build
```

Stop containers and remove volumes:

```bash
docker compose down -v
```

Warning: removing volumes deletes local database data.

## Deployment

Production deployment should use environment variables for all secrets and service configuration.

Recommended deployment requirements:

* Strong randomly generated `SECRET_KEY` and `JWT_SECRET_KEY`
* Strong internal service secret for server-to-service communication
* Secure database credentials with least-privilege database users
* HTTPS-enabled frontend and backend URLs
* Explicit CORS origin whitelist
* Secure cookie settings enabled in production
* Redis available for JWT revocation
* Database and internal services not publicly exposed

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
