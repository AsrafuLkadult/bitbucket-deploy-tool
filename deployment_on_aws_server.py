import os
import logging
from dotenv import load_dotenv
import paramiko
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
SERVER_IP = os.getenv("SERVER_IP")
SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
DEPLOY_PATH = os.getenv("DEPLOY_PATH")
LOCAL_BUILD_PATH = "build"  # Path to your local build files

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_server():
    """Connect to the server using SSH."""
    try:
        logger.info("Connecting to the server...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER_IP, username=SSH_USERNAME, password=SSH_PASSWORD)
        logger.info("Connected to the server successfully.")
        return ssh
    except Exception as e:
        logger.error(f"Failed to connect to the server: {e}")
        raise

def transfer_files(ssh):
    """Transfer build files to the server using SFTP."""
    try:
        logger.info("Transferring files to the server...")
        sftp = ssh.open_sftp()

        # Create a temporary directory on the server
        temp_dir = f"{DEPLOY_PATH}_temp"
        ssh.exec_command(f"mkdir -p {temp_dir}")

        # Copy files from local to server
        for root, dirs, files in os.walk(LOCAL_BUILD_PATH):
            for file in files:
                local_path = os.path.join(root, file)
                remote_path = os.path.join(temp_dir, os.path.relpath(local_path, LOCAL_BUILD_PATH))
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p {remote_dir}")  # Ensure remote directory exists
                sftp.put(local_path, remote_path)
                logger.info(f"Transferred {local_path} to {remote_path}")

        sftp.close()
        logger.info("File transfer completed.")
    except Exception as e:
        logger.error(f"Failed to transfer files: {e}")
        raise

def switch_to_new_version(ssh):
    """Switch to the new version by replacing the old deployment with the new one."""
    try:
        logger.info("Switching to the new version...")
        temp_dir = f"{DEPLOY_PATH}_temp"
        backup_dir = f"{DEPLOY_PATH}_backup"

        # Backup the current deployment
        ssh.exec_command(f"mv {DEPLOY_PATH} {backup_dir}")

        # Move the new deployment to the target directory
        ssh.exec_command(f"mv {temp_dir} {DEPLOY_PATH}")

        # Remove the backup (optional)
        ssh.exec_command(f"rm -rf {backup_dir}")

        logger.info("Switched to the new version successfully.")
    except Exception as e:
        logger.error(f"Failed to switch to the new version: {e}")
        # Rollback to the previous version
        logger.info("Attempting rollback...")
        ssh.exec_command(f"mv {backup_dir} {DEPLOY_PATH}")
        logger.info("Rollback completed.")
        raise

def restart_server_services(ssh):
    """Restart server services (e.g., web server, application server)."""
    try:
        logger.info("Restarting server services...")
        ssh.exec_command("sudo systemctl restart nginx")  # Example: Restart Nginx
        ssh.exec_command("sudo systemctl restart gunicorn")  # Example: Restart Gunicorn
        logger.info("Server services restarted successfully.")
    except Exception as e:
        logger.error(f"Failed to restart server services: {e}")
        raise

def main():
    try:
        logger.info("🚀 Starting auto-deployment script...")

        # Connect to the server
        ssh = connect_to_server()

        # Transfer files to the server
        transfer_files(ssh)

        # Switch to the new version
        switch_to_new_version(ssh)

        # Restart server services
        restart_server_services(ssh)

        logger.info("✅ Deployment completed successfully.")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
    finally:
        # Close the SSH connection
        if ssh:
            ssh.close()
            logger.info("SSH connection closed.")

if __name__ == "__main__":
    main()
