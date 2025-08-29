#!/bin/bash
# Check DNS propagation for portal-anwalts.ai

echo "🌐 Checking DNS propagation for portal-anwalts.ai..."

echo "1. DNS lookup from server:"
nslookup portal-anwalts.ai 8.8.8.8

echo ""
echo "2. DNS lookup from another server:"
nslookup portal-anwalts.ai 1.1.1.1

echo ""
echo "3. Checking root domain:"
dig portal-anwalts.ai A

echo ""
echo "4. Checking www subdomain:"
dig www.portal-anwalts.ai A

echo ""
echo "5. Checking DNS authority:"
dig portal-anwalts.ai NS

echo ""
echo "🔍 DNS diagnosis complete."