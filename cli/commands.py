import click
import requests

from auth import clear_tokens, load_tokens, save_tokens

def api_error(e: requests.RequestException) -> click.ClickException:
    if e.response is None:
        return click.ClickException(f"Could not reach the API at {e.request.url}: {e}")
    try:
        detail = e.response.json()["detail"]
    except (ValueError, KeyError, TypeError):
        detail = f"{e.response.status_code}: {e.response.text[:100]}"
    return click.ClickException(str(detail))

def api_request(ctx: click.Context, method: str, path: str, **kwargs) -> requests.Response:
    url = f"{ctx.obj['api_url']}{path}"
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    try:
        res = requests.request(method, url, headers=headers, timeout=5, **kwargs)
        if res.status_code == 401 and tokens.get("refresh_token"):
            refresh_res = requests.post(
                f"{ctx.obj['api_url']}/refresh-token",
                json={"refresh_token": tokens["refresh_token"]},
                timeout=5,
            )
            if refresh_res.ok:
                data = refresh_res.json()
                save_tokens(data["access_token"], data["refresh_token"])
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                res = requests.request(method, url, headers=headers, timeout=5, **kwargs)
            else:
                clear_tokens()
        res.raise_for_status()
    except requests.RequestException as e:
        raise api_error(e)
    return res

@click.command()
@click.option("--username", "-u", prompt=True, help="API username.")
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    help="API password.",
)
@click.pass_context
def login(ctx: click.Context, username: str, password: str):
    url = f"{ctx.obj['api_url']}/login"
    try:
        res = requests.post(
            url,
            data={"username": username, "password": password},
            timeout=5,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        err = api_error(e)
        if e.response is not None and e.response.status_code == 403:
            err.message += " Run `journal resend-verify-email` to request a new verification email."
        raise err
    data = res.json()
    save_tokens(data["access_token"], data["refresh_token"])
    print("Login succesful.")

@click.command()
@click.option("--username", "-u", prompt=True, help="API username.")
@click.option("--email", "-e", prompt=True, help="API email address.")
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="API password.",
)
@click.pass_context
def register(ctx: click.Context, username: str, email: str, password: str):
    url = f"{ctx.obj['api_url']}/register"
    try:
        res = requests.post(
            url,
            json={"username": username, "email": email, "password": password},
            timeout=5,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        raise api_error(e)
    print(f"Registered user {res.json()['username']}.")
    print("Check your inbox for a verification email; run `journal resend-verify-email` if it doesn't arrive.")

@click.command()
@click.option("--email", "-e", prompt=True, help="Email address used at registration.")
@click.pass_context
def resend_verify_email(ctx: click.Context, email: str):
    url = f"{ctx.obj['api_url']}/resend-verify-email"
    try:
        res = requests.post(url, json={"email": email}, timeout=5)
        res.raise_for_status()
    except requests.RequestException as e:
        raise api_error(e)
    print(res.json()["detail"])

@click.command()
@click.pass_context
def logout(ctx: click.Context):
    refresh_token = load_tokens().get("refresh_token")
    if refresh_token:
        try:
            requests.post(
                f"{ctx.obj['api_url']}/logout",
                json={"refresh_token": refresh_token},
                timeout=5,
            )
        except requests.RequestException:
            pass
    clear_tokens()
    print("Logged out.")

@click.command("list")
@click.pass_context
def list_journals(ctx: click.Context):
    after_id = 0
    while True:
        res = api_request(ctx, "get", "/api/journal", params={"after_id": after_id})
        try:
            page_size = int(res.headers["X-Page-Size"])
        except (KeyError, ValueError):
            raise click.ClickException("API did not return a valid X-Page-Size header.")
        entries = res.json()
        if not entries:
            if after_id == 0:
                print("No entries found.")
            break
        for entry in entries:
            print(f"{entry['id']}: {entry['title']}")
        after_id = entries[-1]["id"]
        if len(entries) < page_size:
            break
        print("Show next page? [Y/n] ", end="", flush=True)
        key = click.getchar()
        print(key)
        if key.lower() == "n":
            break

@click.command()
@click.pass_context
def index(ctx: click.Context):
    url = f"{ctx.obj['api_url']}/api/journal/index"
    after_id = 0
    while True:
        try:
            res = requests.get(url, params={"after_id": after_id}, timeout=5)
            res.raise_for_status()
        except requests.RequestException as e:
            raise api_error(e)
        try:
            page_size = int(res.headers["X-Page-Size"])
        except (KeyError, ValueError):
            raise click.ClickException("API did not return a valid X-Page-Size header.")
        entries = res.json()
        if not entries:
            if after_id == 0:
                print("No entries found.")
            break
        for entry in entries:
            print(f"{entry['id']}: {entry['title']}")
        after_id = entries[-1]["id"]
        if len(entries) < page_size:
            break
        print("Show next page? [Y/n] ", end="", flush=True)
        key = click.getchar()
        print(key)
        if key.lower() == "n":
            break

@click.command()
@click.argument("journal_id", type=int)
@click.pass_context
def get(ctx: click.Context, journal_id: int):
    res = api_request(ctx, "get", f"/api/journal/{journal_id}")
    data = res.json()
    print(f"Title: {data['title']}")
    print(f"Body: {data['body']}")

@click.command()
@click.argument("journal_id", type=int)
@click.pass_context
def delete(ctx: click.Context, journal_id: int):
    api_request(ctx, "delete", f"/api/journal/{journal_id}")
    print(f"Deleted entry {journal_id}")

@click.command()
@click.option("--title", prompt=True, help="Title of the journal entry.")
@click.option("--body", prompt=True, help="Body of the journal entry.")
@click.option("--public/--private", "is_public", default=False,
              help="Publish the entry so anyone can read it.")
@click.pass_context
def create(ctx: click.Context, title: str, body: str, is_public: bool):
    res = api_request(ctx, "post", "/api/journal/create", json={"title": title, "body": body, "is_public": is_public})
    data = res.json()
    print(f"Created entry {data['id']}: {data['title']}")

@click.command()
@click.argument("journal_id", type=int)
@click.option("--title", prompt=True, help="Title of the journal entry.")
@click.option("--body", prompt=True, help="Body of the journal entry.")
@click.option("--public/--private", "is_public", default=None,
              help="Publish or unpublish the entry (defaults to keeping its current setting).")
@click.pass_context
def replace(
    ctx: click.Context,
    journal_id: int,
    title: str,
    body: str,
    is_public: bool | None,
):
    if is_public is None:
        is_public = api_request(ctx, "get", f"/api/journal/{journal_id}").json()["is_public"]
    res = api_request(ctx, "put", f"/api/journal/{journal_id}", json={"title": title, "body": body, "is_public": is_public})
    data = res.json()
    print(f"Replaced entry {data['id']}: {data['title']}")

@click.command()
@click.argument("journal_id", type=int)
@click.option(
    "--title",
    prompt=True,
    default="",
    show_default=False,
    help="New title of the journal entry (leave blank to keep unchanged).",
)
@click.option(
    "--body",
    prompt=True,
    default="",
    show_default=False,
    help="New body of the journal entry (leave blank to keep unchanged).",
)
@click.option("--public/--private", "is_public", default=None,
              help="Publish or unpublish the entry (leave unset to keep unchanged).")
@click.pass_context
def update(
    ctx: click.Context,
    journal_id: int,
    title: str | None,
    body: str | None,
    is_public: bool | None,
):
    payload = {k: v for k, v in {"title": title, "body": body}.items() if v}
    if is_public is not None:
        payload["is_public"] = is_public
    if not payload:
        raise click.UsageError("Provide at least one of --title, --body, or --public/--private.")
    res = api_request(ctx, "patch", f"/api/journal/{journal_id}", json=payload)
    data = res.json()
    print(f"Updated entry {data['id']}: {data['title']}")
