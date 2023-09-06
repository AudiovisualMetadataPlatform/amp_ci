from pydantic import BaseModel, Field
from typing import Union

#
# JSON data to github
#
class WebhookResponse(BaseModel):
    result: str

#
# JSON data from Github
#
class Hook(BaseModel):
    type: str
    id: int
    name: str
    active: bool
    events: list[str]
    config: dict
    updated_at: str
    created_at: str
    url: str
    ping_url: str
    deliveries_url: str

class Organization(BaseModel):
    login: str
    id: int
    node_id: str
    url: str
    repos_url: str
    # The rest of the URL strings we don't care about.
    # events_url, hooks_url, issues_url, members_url, public_members_url, avatar_url    
    description: str


class Sender(BaseModel):
    login: str
    id: int
    node_id: str
    # A bunch of URL/strings we don't care about:
    # avatar_url, gravatar_id, url, html_url, followers_url, following_url,
    # gists_url, starred_url, subscriptions_url, organizations_url,
    # repos_url, events_url, received_events_url
    type: str
    site_admin: bool


class WebhookPing(BaseModel):
    zen: str
    hook_id: int
    hook: Hook
    organization: Organization
    sender: Sender


class Owner(BaseModel):
    name: str
    email: str
    login: str
    id: int
    node_id: str
    type: str
    site_admin: bool
    # Other fields I don't care about:
    # avatar_url, gravatar_url, url, html_url, followers_url,
    # following_url, gists_url, starred_url, subscriptions_url,
    # organizations_url, repos_url, events_url, received_events_url,

class Repository(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: Owner
    description: str
    fork: bool
    url: str
    # Other fields I don't care about:
    # html_url, forks_url, keys_url, collaborators_url, teams_url, hooks_url,
    # issue_events_url, events_url, assignees_url, branches_url, tags_url,
    # blobs_url, git_tags_url, git_refs_url, trees_url, statuses_url, 
    # languages_url, stargazers_url, contributers_url, subscribers_url,
    # subscription_url, commits-url, git_commits_url, comments_url,
    # issue_comment_url, contents_url, compare_url, merges_url, archive_url,
    # downloads_url, issues_url, pulls_url, milestones_url, notifications_url,
    # labels_url, releases_url, deployments_url
    # git_url, ssh_url, svn_url, homepage, size, stargazers_count, 
    # watchers_count, language, has_issues, has_projects, has_downloads,
    # has_wiki, has_pages, has_discussions, forks_count, mirror_url, archived,
    # disabled, open_issues_count, license, allow_forking, is_template, 
    # web_commit_signoff_requried, topics, visibility, forks open_issues,
    # watchers, stargazers, organization
    created_at: int
    updated_at: str
    pushed_at: int
    clone_url: str
    default_branch: str
    master_branch: str


class Pusher(BaseModel):
    name: str
    email: str


class WebhookPush(BaseModel):
    ref: str
    before: str
    after: str
    repository: Repository
    pusher: Pusher
    organization: Organization
    sender: Sender

class ManualRebuild(BaseModel):
    class ManualRepository(BaseModel):
        name: str
    
    class ManualPusher(BaseModel):
        name: str
        email: str

    ref: str
    repository: ManualRepository
    pusher: ManualPusher


#
# Configuration file
#
class Repo(BaseModel):
    build: bool = True
    deps: list[str] = Field(default_factory=list)


class ConfigFile(BaseModel):
    host: str
    port: int
    workers: int = 1
    workdir: str = "/tmp"
    baseurl: str
    scripts: dict[str,list[str]] 
    temproot: str
    repos: list[str]

