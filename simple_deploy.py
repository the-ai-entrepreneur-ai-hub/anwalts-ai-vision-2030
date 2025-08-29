import subprocess
import time

def deploy_to_server():
    """Deploy navigation fix and restart backend"""
    print("Deploying fixes to server...")
    
    # Create deployment commands
    commands = [
        # Upload navigation fix
        'pscp -pw "8sKHWH5cVu5fb3" fix_navigation_auth_issue.js root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/',
        
        # Kill existing backend and restart with API key
        'echo pkill -f uvicorn | plink -pw "8sKHWH5cVu5fb3" root@148.251.195.222',
        'echo "cd /var/www/portal-anwalts.ai/backend && export TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720 && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &" | plink -pw "8sKHWH5cVu5fb3" root@148.251.195.222'
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            print(f"Command: {cmd[:50]}...")
            print(f"Result: {result.returncode}")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            time.sleep(2)
        except Exception as e:
            print(f"Error running command: {e}")
    
    print("Deployment complete!")

if __name__ == "__main__":
    deploy_to_server()