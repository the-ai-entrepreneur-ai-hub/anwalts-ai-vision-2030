#!/bin/bash
# Diagnose server connectivity issues

echo "🔍 Diagnosing Server Connectivity..."

echo "1. Checking if nginx is listening on port 80:"
netstat -tlnp | grep :80

echo ""
echo "2. Checking if any firewall is blocking port 80:"
iptables -L -n | grep -E "(80|ACCEPT|DROP|REJECT)"

echo ""
echo "3. Testing local connections:"
echo "   Local HTTP test:"
curl -I http://localhost
echo "   Local domain test:"
curl -I -H "Host: portal-anwalts.ai" http://localhost

echo ""
echo "4. Checking server's external IP:"
hostname -I

echo ""
echo "5. Checking if server can reach itself externally:"
curl -I --connect-timeout 5 http://148.251.195.222

echo ""
echo "6. Checking what's listening on all interfaces:"
ss -tlnp | grep :80

echo ""
echo "7. System info:"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "   Kernel: $(uname -r)"

echo ""
echo "🔍 Diagnosis complete. This will help identify the connectivity issue."