import os
import shutil
import subprocess
import logging
from git import Repo
from dotenv import load_dotenv
from pathlib import Path


# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
username = os.getenv("BITBUCKET_USERNAME")
app_password = os.getenv("BITBUCKET_APP_PASSWORD")
release_version = os.getenv('RELEASE_VERSION')

# Define repository URLs
jupiter_main_repo_url = f"https://{username}:{app_password}@bitbucket.org/sicunet1/jupiter-main-web.git"
backend_repo_url = f"https://{username}:{app_password}@bitbucket.org/sicunet1/jupiter-backend.git"
frontend_repo_url = f"https://{username}:{app_password}@bitbucket.org/sicunet1/jupiter-frontend.git"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_step(step_name):
    """Log the start and end of a step with visual separators."""
    logger.info(f"\n=== {step_name.upper()} [START] ===")

def log_completion(step_name):
    """Log the completion of a step."""
    logger.info(f"=== {step_name.upper()} [COMPLETED] ===\n")

def run_command(command, cwd=None):
    """Run a terminal command."""
    logger.info(f"[PROCESSING] Running command: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"[ERROR] Command failed: {command}\n{result.stderr}")
        raise Exception(f"Command failed: {command}")
    else:
        logger.info(f"[SUCCESS] Command output:\n{result.stdout}")

def check_code_already_exists(repo_name):
    """Check if a directory starting with the repo name exists."""
    current_dir = Path('.')
    matching_dirs = [d for d in current_dir.iterdir() if d.is_dir() and d.name.startswith(repo_name)]
    return bool(matching_dirs)

def clone_or_pull_frontend_repo():
    """Clone or pull the frontend repository."""
    log_step("Cloning or pulling frontend repository")
    if check_code_already_exists("frontend"):
        logger.info("Frontend repo already exists. Pulling latest changes...")
        repo_dir = os.path.join(os.getcwd(), 'frontend')
        repo = Repo(repo_dir)
        origin = repo.remote(name='origin')
        repo.git.checkout('main')
        origin.pull()
    else:
        logger.info("Cloning frontend repository...")
        Repo.clone_from(frontend_repo_url, "frontend")
    log_completion("Cloning or pulling frontend repository")

def build_frontend():
    """Build the frontend using npm commands."""
    log_step("Building frontend")
    frontend_path = os.path.join(os.getcwd(), 'frontend')
    if not check_code_already_exists("jupiter"):
        run_command("npm i --force", cwd=frontend_path)
    run_command("npm run build", cwd=frontend_path)
    log_completion("Building frontend")

def clone_or_pull_backend_repo():
    """Clone or pull the backend repository."""
    log_step("Cloning or pulling backend repository")
    if check_code_already_exists("backend"):
        logger.info("Backend repo already exists. Pulling latest changes...")
        repo_dir = os.path.join(os.getcwd(), 'backend')
        repo = Repo(repo_dir)
        origin = repo.remote(name='origin')
        repo.git.checkout('master')
        origin.pull()
    else:
        logger.info("Cloning backend repository...")
        Repo.clone_from(backend_repo_url, "backend")
    log_completion("Cloning or pulling backend repository")

def clone_or_pull_jupiter_main_repo():
    """Clone or pull the jupiter main repository."""
    log_step("Cloning or pulling jupiter main repository")
    if check_code_already_exists("main_repo"):
        logger.info("Jupiter main repo already exists. Pulling latest changes...")
        repo_dir = os.path.join(os.getcwd(), 'main_repo')
        repo = Repo(repo_dir)
        origin = repo.remote(name='origin')
        repo.git.checkout('master')
        origin.pull()
    else:
        logger.info("Cloning jupiter main repository...")
        Repo.clone_from(jupiter_main_repo_url, "main_repo")
    log_completion("Cloning or pulling jupiter main repository")

def update_static_and_files():
    """Update static files and necessary directories in the main repository."""
    log_step("Updating static and backend files in main repository")
    # Define paths
    static_path = os.path.join(os.getcwd(), 'jupiter')
    backend_path = os.path.join(os.getcwd(), 'backend')
    main_repo_path = os.path.join(os.getcwd(), 'main_repo')
    main_static_path = os.path.join(main_repo_path, 'static')
    main_apps_path = os.path.join(main_repo_path, 'apps')
    main_jupiter_path = os.path.join(main_repo_path, 'jupiter')
    main_templates_path = os.path.join(main_repo_path, 'templates')

    # Remove old files and directories
    for path in [main_static_path, main_apps_path, main_jupiter_path, main_templates_path]:
        if os.path.exists(path):
            logger.info(f"Removing old files from {path}")
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    # Copy new files and directories
    shutil.copytree(os.path.join(static_path, "static"), main_static_path, dirs_exist_ok=True)
    shutil.copytree(os.path.join(backend_path, "apps"), main_apps_path, dirs_exist_ok=True)
    shutil.copytree(os.path.join(backend_path, "jupiter"), main_jupiter_path, dirs_exist_ok=True)
    shutil.copytree(os.path.join(backend_path, "templates"), main_templates_path, dirs_exist_ok=True)

    log_completion("Updating static and backend files in main repository")

def commit_and_push_changes():
    """Commit and push changes to the main repository."""
    log_step("Committing and pushing changes")
    repo_dir = os.path.join(os.getcwd(), "main_repo")
    repo = Repo(repo_dir)
    origin = repo.remote(name='origin')
    origin.pull()
    repo.git.add(A=True)
    repo.index.commit(f"Release version {release_version}")
    origin.push()
    log_completion("Committing and pushing changes")

def main():
    try:
        logger.info("\n🚀 Starting auto deployment script...")
        clone_or_pull_frontend_repo()
        build_frontend()
        clone_or_pull_backend_repo()
        clone_or_pull_jupiter_main_repo()
        update_static_and_files()
        commit_and_push_changes()
        logger.info("✅ All tasks completed successfully.")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()