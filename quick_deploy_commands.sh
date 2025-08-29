#!/bin/bash

echo "=========================================="
echo "  AnwaltsAI Hetzner Server Deployment"
echo "=========================================="
echo ""
echo "Server: 148.251.195.222"
echo "Owner: Dr. Markus Weigl, AIgenex GmbH"
echo "Dataset: 9,997 German legal examples"
echo ""

echo "Choose deployment method:"
echo "1. Upload ZIP file (Recommended)"
echo "2. Upload directory directly"  
echo "3. Show manual commands"
echo ""

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Uploading ZIP file to server..."
        echo "Command: scp \"anwalts-ai-deployment-Law Firm Vision 2030.zip\" root@148.251.195.222:/opt/"
        echo ""
        
        if scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/; then
            echo ""
            echo "ZIP uploaded successfully!"
            echo ""
            echo "Next steps:"
            echo "1. SSH into server: ssh root@148.251.195.222"
            echo "2. Password: BrfiDiUwxFEAvu"
            echo "3. Extract: cd /opt && unzip \"anwalts-ai-deployment-Law Firm Vision 2030.zip\""
            echo "4. Deploy: cd deployment_package && chmod +x deploy.sh && ./deploy.sh"
        else
            echo "Upload failed. Try manual method or check connection."
        fi
        ;;
        
    2)
        echo ""
        echo "Uploading deployment directory..."
        echo "Command: scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/"
        echo ""
        
        if scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/; then
            echo ""
            echo "Directory uploaded successfully!"
            echo ""
            echo "Next steps:"
            echo "1. SSH into server: ssh root@148.251.195.222"
            echo "2. Password: BrfiDiUwxFEAvu"
            echo "3. Deploy: cd /opt/anwalts-ai && chmod +x deploy.sh && ./deploy.sh"
        else
            echo "Upload failed. Try manual method or check connection."
        fi
        ;;
        
    3)
        echo ""
        echo "=========================================="
        echo "  Manual Deployment Commands"
        echo "=========================================="
        echo ""
        echo "1. Upload ZIP file:"
        echo "   scp \"anwalts-ai-deployment-Law Firm Vision 2030.zip\" root@148.251.195.222:/opt/"
        echo ""
        echo "2. OR Upload directory:"
        echo "   scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/"
        echo ""
        echo "3. SSH into server:"
        echo "   ssh root@148.251.195.222"
        echo "   Password: BrfiDiUwxFEAvu"
        echo ""
        echo "4. If you uploaded ZIP:"
        echo "   cd /opt"
        echo "   unzip \"anwalts-ai-deployment-Law Firm Vision 2030.zip\""
        echo "   cd deployment_package"
        echo ""
        echo "5. If you uploaded directory:"
        echo "   cd /opt/anwalts-ai"
        echo ""
        echo "6. Deploy:"
        echo "   chmod +x deploy.sh"
        echo "   ./deploy.sh"
        echo ""
        echo "7. Verify deployment:"
        echo "   Access: http://148.251.195.222"
        echo "   API: http://148.251.195.222/api/docs"
        echo "   Health: http://148.251.195.222/health"
        echo ""
        ;;
        
    *)
        echo "Invalid choice. Please run again and select 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo "Deployment package ready with 9,997 German legal examples!"
echo "Application will be available at: http://148.251.195.222"
echo ""