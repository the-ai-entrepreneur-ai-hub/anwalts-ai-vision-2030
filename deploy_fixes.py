#!/usr/bin/env python3
"""
Deploy fixes to the server using Python
"""
import subprocess
import os
import sys

def run_command(cmd, password="8sKHWH5cVu5fb3"):
    """Run SSH command with password"""
    try:
        # Use expect script approach
        expect_script = f'''
#!/usr/bin/expect -f
set timeout 30
spawn {cmd}
expect "password:"
send "{password}\\r"
expect eof
'''
        
        with open("temp_expect.exp", "w") as f:
            f.write(expect_script)
        
        os.chmod("temp_expect.exp", 0o755)
        result = subprocess.run(["./temp_expect.exp"], capture_output=True, text=True)
        os.remove("temp_expect.exp")
        
        return result
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def main():
    print("🚀 Deploying fixes to server...")
    
    # 1. Upload navigation fix
    print("📤 Uploading navigation fix...")
    result = run_command('scp -o StrictHostKeyChecking=no fix_navigation_auth_issue.js root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/')
    if result and result.returncode == 0:
        print("✅ Navigation file uploaded")
    else:
        print("❌ Failed to upload navigation file")
    
    # 2. Restart backend with API key
    print("🔄 Restarting backend with API key...")
    backend_commands = [
        "pkill -f uvicorn",
        "cd /var/www/portal-anwalts.ai/backend",
        "export TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720",
        "nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &"
    ]
    
    cmd = f'ssh -o StrictHostKeyChecking=no root@148.251.195.222 "{"; ".join(backend_commands)}"'
    result = run_command(cmd)
    
    if result and result.returncode == 0:
        print("✅ Backend restarted with API key")
    else:
        print("❌ Failed to restart backend")
    
    # 3. Test endpoints
    print("🧪 Testing endpoints...")
    test_cmd = 'ssh -o StrictHostKeyChecking=no root@148.251.195.222 "curl -X GET http://localhost:8000/health"'
    result = run_command(test_cmd)
    
    if result:
        print("📋 Health check result:", result.stdout)
    
    print("🎉 Deployment complete!")

if __name__ == "__main__":
    main()