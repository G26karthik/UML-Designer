"""
Git Utility Module
Provides Git operations for repository analysis
"""

import os
import subprocess
import logging
import tempfile
import shutil
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class GitUtils:
    """Utility class for Git operations"""
    
    @staticmethod
    def is_git_repository(path: str) -> bool:
        """
        Check if path is a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if Git repository, False otherwise
        """
        git_dir = os.path.join(path, '.git')
        return os.path.isdir(git_dir)
    
    @staticmethod
    def is_git_url(url: str) -> bool:
        """
        Check if string is a Git URL.
        
        Args:
            url: String to check
            
        Returns:
            True if Git URL, False otherwise
        """
        git_patterns = [
            url.startswith('https://github.com/'),
            url.startswith('https://gitlab.com/'),
            url.startswith('https://bitbucket.org/'),
            url.startswith('git@github.com:'),
            url.startswith('git@gitlab.com:'),
            url.endswith('.git'),
        ]
        return any(git_patterns)
    
    @staticmethod
    def clone_repository(git_url: str, target_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Clone a Git repository.
        
        Args:
            git_url: Git URL to clone
            target_dir: Target directory (optional, creates temp dir if not provided)
            
        Returns:
            Tuple of (success, directory_path)
        """
        try:
            # Create target directory if not provided
            if not target_dir:
                target_dir = tempfile.mkdtemp(prefix='git_clone_')
            
            logger.info(f"Cloning repository: {git_url}")
            
            # Clone repository
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', git_url, target_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned to: {target_dir}")
                return True, target_dir
            else:
                logger.error(f"Git clone failed: {result.stderr}")
                return False, ""
                
        except subprocess.TimeoutExpired:
            logger.error("Git clone timeout")
            return False, ""
        except FileNotFoundError:
            logger.error("Git not found. Please install Git.")
            return False, ""
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False, ""
    
    @staticmethod
    def get_repository_info(repo_path: str) -> dict:
        """
        Get information about Git repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with repository information
        """
        info = {
            'is_git_repo': False,
            'remote_url': None,
            'branch': None,
            'commit_count': 0,
            'last_commit': None
        }
        
        if not GitUtils.is_git_repository(repo_path):
            return info
        
        info['is_git_repo'] = True
        
        try:
            # Get remote URL
            result = subprocess.run(
                ['git', '-C', repo_path, 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info['remote_url'] = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(
                ['git', '-C', repo_path, 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info['branch'] = result.stdout.strip()
            
            # Get commit count
            result = subprocess.run(
                ['git', '-C', repo_path, 'rev-list', '--count', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info['commit_count'] = int(result.stdout.strip())
            
            # Get last commit
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', '-1', '--pretty=%H|%an|%ae|%ad|%s'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) == 5:
                    info['last_commit'] = {
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    }
        
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
        
        return info
    
    @staticmethod
    def extract_github_info(url: str) -> Optional[dict]:
        """
        Extract owner and repo name from GitHub URL.
        
        Args:
            url: GitHub URL
            
        Returns:
            Dictionary with owner and repo, or None if not valid
        """
        try:
            # Handle different GitHub URL formats
            url = url.rstrip('/')
            
            # HTTPS format: https://github.com/owner/repo
            if 'github.com/' in url:
                parts = url.split('github.com/')
                if len(parts) == 2:
                    path_parts = parts[1].rstrip('.git').split('/')
                    if len(path_parts) >= 2:
                        return {
                            'owner': path_parts[0],
                            'repo': path_parts[1],
                            'full_name': f"{path_parts[0]}/{path_parts[1]}"
                        }
            
            # SSH format: git@github.com:owner/repo.git
            if 'git@github.com:' in url:
                parts = url.split('git@github.com:')
                if len(parts) == 2:
                    path = parts[1].rstrip('.git')
                    path_parts = path.split('/')
                    if len(path_parts) >= 2:
                        return {
                            'owner': path_parts[0],
                            'repo': path_parts[1],
                            'full_name': f"{path_parts[0]}/{path_parts[1]}"
                        }
        
        except Exception as e:
            logger.error(f"Error parsing GitHub URL: {e}")
        
        return None
    
    @staticmethod
    def get_file_history(repo_path: str, file_path: str, max_commits: int = 10) -> list:
        """
        Get commit history for a specific file.
        
        Args:
            repo_path: Path to repository
            file_path: Path to file (relative to repo)
            max_commits: Maximum number of commits to return
            
        Returns:
            List of commit dictionaries
        """
        commits = []
        
        try:
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', f'-{max_commits}', 
                 '--pretty=%H|%an|%ad|%s', '--', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) == 4:
                            commits.append({
                                'hash': parts[0],
                                'author': parts[1],
                                'date': parts[2],
                                'message': parts[3]
                            })
        
        except Exception as e:
            logger.error(f"Error getting file history: {e}")
        
        return commits
    
    @staticmethod
    def get_changed_files(repo_path: str, since_commit: Optional[str] = None) -> list:
        """
        Get list of changed files.
        
        Args:
            repo_path: Path to repository
            since_commit: Commit hash to compare from (optional)
            
        Returns:
            List of changed file paths
        """
        changed_files = []
        
        try:
            if since_commit:
                cmd = ['git', '-C', repo_path, 'diff', '--name-only', since_commit, 'HEAD']
            else:
                cmd = ['git', '-C', repo_path, 'diff', '--name-only']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
        
        return changed_files
    
    @staticmethod
    def cleanup_temp_repo(repo_path: str):
        """
        Clean up temporary cloned repository.
        
        Args:
            repo_path: Path to repository to delete
        """
        try:
            if os.path.exists(repo_path) and os.path.isdir(repo_path):
                # Check if it's a temp directory to avoid accidents
                if 'tmp' in repo_path or 'temp' in repo_path or 'git_clone' in repo_path:
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up temp repository: {repo_path}")
                else:
                    logger.warning(f"Refusing to delete non-temp directory: {repo_path}")
        except Exception as e:
            logger.error(f"Error cleaning up repository: {e}")
    
    @staticmethod
    def get_repository_stats(repo_path: str) -> dict:
        """
        Get statistics about Git repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_commits': 0,
            'total_contributors': 0,
            'first_commit_date': None,
            'last_commit_date': None,
            'total_branches': 0
        }
        
        if not GitUtils.is_git_repository(repo_path):
            return stats
        
        try:
            # Total commits
            result = subprocess.run(
                ['git', '-C', repo_path, 'rev-list', '--count', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                stats['total_commits'] = int(result.stdout.strip())
            
            # Total contributors
            result = subprocess.run(
                ['git', '-C', repo_path, 'shortlog', '-sn', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                stats['total_contributors'] = len(result.stdout.strip().split('\n'))
            
            # First commit date
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', '--reverse', '--pretty=%ad', '--date=short'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    stats['first_commit_date'] = lines[0]
            
            # Last commit date
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', '-1', '--pretty=%ad', '--date=short'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                stats['last_commit_date'] = result.stdout.strip()
            
            # Total branches
            result = subprocess.run(
                ['git', '-C', repo_path, 'branch', '-a'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                stats['total_branches'] = len(result.stdout.strip().split('\n'))
        
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
        
        return stats
