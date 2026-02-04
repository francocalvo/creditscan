# FastAPI Project - Deployment

You can deploy the project using Docker Compose to a remote server.

This project expects you to have a Traefik proxy handling communication to the
outside world and HTTPS certificates.

## Public Traefik

We need a Traefik proxy to handle incoming connections and HTTPS certificates.

You need to do these next steps only once.

### Traefik Public Network

This Traefik will expect a Docker "public network" named `traefik-public` to
communicate with your stack(s).

This way, there will be a single public Traefik proxy that handles the
communication (HTTP and HTTPS) with the outside world, and then behind that, you
could have one or more stacks with different domains, even if they are on the
same single server.

To create a Docker "public network" named `traefik-public` run the following
command in your remote server:

```bash
docker network create traefik-public
```

### Traefik Environment Variables

The Traefik Docker Compose file expects some environment variables to be set in
your terminal before starting it. You can do it by running the following
commands in your remote server.

- Create the username for HTTP Basic Auth, e.g.:

```bash
export USERNAME=admin
```

- Create an environment variable with the password for HTTP Basic Auth, e.g.:

```bash
export PASSWORD=changethis
```

- Use openssl to generate the "hashed" version of the password for HTTP Basic
  Auth and store it in an environment variable:

```bash
export HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)
```

To verify that the hashed password is correct, you can print it:

```bash
echo $HASHED_PASSWORD
```

- Create an environment variable with the domain name for your server, e.g.:

```bash
export DOMAIN=fastapi-project.example.com
```

- Create an environment variable with the email for Let's Encrypt, e.g.:

```bash
export EMAIL=admin@example.com
```

**Note**: you need to set a different email, an email `@example.com` won't work.

### Start the Traefik Docker Compose

Go to the directory where you copied the Traefik Docker Compose file in your
remote server:

```bash
cd /root/code/traefik-public/
```

Now with the environment variables set and the `docker-compose.traefik.yml` in
place, you can start the Traefik Docker Compose running the following command:

```bash
docker compose -f docker-compose.traefik.yml up -d
```

## Environment Variables

You need to set some environment variables first.

Set the `ENVIRONMENT`, by default `local` (for development), but when deploying
to a server you would put something like `staging` or `production`:

```bash
export ENVIRONMENT=production
```

Set the `DOMAIN`, by default `localhost` (for development), but when deploying
you would use your own domain, for example:

```bash
export DOMAIN=fastapi-project.example.com
```

You can set several variables, like:

- `PROJECT_NAME`: The name of the project, used in the API for the docs and
  emails.
- `STACK_NAME`: The name of the stack used for Docker Compose labels and project
  name, this should be different for `staging`, `production`, etc. You could use
  the same domain replacing dots with dashes, e.g. `fastapi-project-example-com`
  and `staging-fastapi-project-example-com`.
- `BACKEND_CORS_ORIGINS`: A list of allowed CORS origins separated by commas.
- `SECRET_KEY`: The secret key for the FastAPI project, used to sign tokens.
- `FIRST_SUPERUSER`: The email of the first superuser, this superuser will be
  the one that can create new users.
- `FIRST_SUPERUSER_PASSWORD`: The password of the first superuser.
- `SMTP_HOST`: The SMTP server host to send emails, this would come from your
  email provider (E.g. Mailgun, Sparkpost, Sendgrid, etc).
- `SMTP_USER`: The SMTP server user to send emails.
- `SMTP_PASSWORD`: The SMTP server password to send emails.
- `EMAILS_FROM_EMAIL`: The email account to send emails from.
- `POSTGRES_SERVER`: The hostname of the PostgreSQL server. You can leave the
  default of `db`, provided by the same Docker Compose. You normally wouldn't
  need to change this unless you are using a third-party provider.
- `POSTGRES_PORT`: The port of the PostgreSQL server. You can leave the default.
  You normally wouldn't need to change this unless you are using a third-party
  provider.
- `POSTGRES_PASSWORD`: The Postgres password.
- `POSTGRES_USER`: The Postgres user, you can leave the default.
- `POSTGRES_DB`: The database name to use for this application. You can leave
  the default of `app`.

### Deploy with Docker Compose

With the environment variables in place, you can deploy with Docker Compose:

```bash
docker compose -f docker-compose.yml up -d
```

## Garage (S3-compatible storage)

This stack includes a [Garage](https://garagehq.deuxfleurs.fr/) service that provides an S3-compatible API for storing uploaded PDFs.

Key points:

- Garage uses `garage.toml` for its configuration and persistent Docker volumes for metadata/data.
- On a fresh install (or after wiping Docker volumes), Garage needs a one-time bootstrap step to assign/apply the cluster layout. Until then it will respond with errors like "Layout not ready".
- If Garage metadata is wiped, buckets/keys may be lost, and the backend will fail with S3 `AccessDenied` / missing-key errors until you re-provision them.

### Bootstrap Garage

After starting the stack, run:

```bash
./scripts/garage-bootstrap.sh
```

This script:

- assigns/applies a single-node layout (if needed)
- ensures the configured bucket exists
- optionally imports an existing access key (if `S3_ACCESS_KEY` + `S3_SECRET_KEY` are set) and grants bucket permissions

### Backend S3 settings

The backend expects these environment variables (typically provided via `.env`/secrets):

- `S3_ENDPOINT_URL`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `S3_REGION`

For containers, `S3_ENDPOINT_URL` should generally be `http://garage:3900`.

### Persistence warning

Avoid `docker compose down -v` on the server unless you intentionally want to wipe Garage state.

For production you wouldn't want to have the overrides in
`docker-compose.override.yml`, that's why we explicitly specify
`docker-compose.yml` as the file to use.

## URLs

Replace `fastapi-project.example.com` with your domain.

### Main Traefik Dashboard

Traefik UI: `https://traefik.fastapi-project.example.com`

### Production

Frontend: `https://dashboard.fastapi-project.example.com`

Backend API docs: `https://api.fastapi-project.example.com/docs`

Backend API base URL: `https://api.fastapi-project.example.com`

Adminer: `https://adminer.fastapi-project.example.com`

### Staging

Frontend: `https://dashboard.staging.fastapi-project.example.com`

Backend API docs: `https://api.staging.fastapi-project.example.com/docs`

Backend API base URL: `https://api.staging.fastapi-project.example.com`

Adminer: `https://adminer.staging.fastapi-project.example.com`
