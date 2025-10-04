#!/usr/bin/env python3
"""
Comprehensive kagent Framework Test Suite
Tests MCP servers, agents, and the full integration
"""

import requests
import json
import sys
import subprocess
import time

class KagentTester:
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def test(self, name, func):
        """Run a test and record results"""
        print(f"\n🧪 Testing: {name}")
        try:
            func()
            print(f"   ✅ PASSED")
            self.results["passed"] += 1
            self.results["tests"].append({"name": name, "status": "PASSED"})
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "status": "FAILED", "error": str(e)})
    
    def kubectl(self, cmd):
        """Execute kubectl command"""
        result = subprocess.run(
            f"kubectl {cmd}",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    
    def test_mcpserver_hello_mcp_exists(self):
        """Test if hello-mcp MCPServer exists"""
        stdout, stderr, code = self.kubectl("get mcpserver hello-mcp -o json")
        assert code == 0, "hello-mcp MCPServer not found"
        data = json.loads(stdout)
        assert data['kind'] == 'MCPServer', "Resource is not a MCPServer"
    
    def test_mcpserver_hello_mcp_ready(self):
        """Test if hello-mcp MCPServer is ready"""
        stdout, stderr, code = self.kubectl("get mcpserver hello-mcp -o json")
        data = json.loads(stdout)
        conditions = data.get('status', {}).get('conditions', [])
        ready = any(c['type'] == 'Ready' and c['status'] == 'True' for c in conditions)
        assert ready, "MCPServer is not ready"
    
    def test_mcpserver_hello_mcp_server_exists(self):
        """Test if hello-mcp-server MCPServer exists"""
        stdout, stderr, code = self.kubectl("get mcpserver hello-mcp-server -o json")
        assert code == 0, "hello-mcp-server MCPServer not found"
    
    def test_mcpserver_hello_mcp_server_ready(self):
        """Test if hello-mcp-server MCPServer is ready"""
        stdout, stderr, code = self.kubectl("get mcpserver hello-mcp-server -o json")
        data = json.loads(stdout)
        conditions = data.get('status', {}).get('conditions', [])
        ready = any(c['type'] == 'Ready' and c['status'] == 'True' for c in conditions)
        assert ready, "MCPServer hello-mcp-server is not ready"
    
    def test_mcpserver_pod_running(self):
        """Test if MCPServer pods are running"""
        stdout, stderr, code = self.kubectl("get pods -n default -o json")
        data = json.loads(stdout)
        pods = [p for p in data.get('items', []) if 'hello-mcp' in p['metadata']['name']]
        assert len(pods) > 0, "No hello-mcp pods found"
        running_pods = [p for p in pods if p['status']['phase'] == 'Running']
        assert len(running_pods) > 0, "No hello-mcp pods are running"
    
    def test_agent_hello_world_exists(self):
        """Test if hello-world-agent exists"""
        stdout, stderr, code = self.kubectl("get agent hello-world-agent -o json")
        assert code == 0, "hello-world-agent not found"
    
    def test_agent_hello_mcp_exists(self):
        """Test if hello-mcp-agent exists"""
        stdout, stderr, code = self.kubectl("get agent hello-mcp-agent -o json")
        assert code == 0, "hello-mcp-agent not found"
    
    def test_model_config_exists(self):
        """Test if gemini-pro ModelConfig exists"""
        stdout, stderr, code = self.kubectl("get modelconfig gemini-pro -o json")
        assert code == 0, "gemini-pro ModelConfig not found"
        data = json.loads(stdout)
        assert data['spec']['model'] == 'gemini-2.5-pro', "Incorrect model"
    
    def test_configmap_hello_mcp_tool_exists(self):
        """Test if hello-mcp-tool ConfigMap exists"""
        stdout, stderr, code = self.kubectl("get configmap hello-mcp-tool -o json")
        assert code == 0, "hello-mcp-tool ConfigMap not found"
        data = json.loads(stdout)
        assert 'hello_mcp.py' in data['data'], "hello_mcp.py not in ConfigMap"
    
    def test_mcp_service_exists(self):
        """Test if MCP server services exist"""
        stdout, stderr, code = self.kubectl("get svc hello-mcp -o json")
        assert code == 0, "hello-mcp service not found"
        data = json.loads(stdout)
        assert data['spec']['ports'][0]['port'] == 3000, "Service port incorrect"
    
    def test_mcp_server_logs(self):
        """Test if MCP server logs show it's running"""
        # Get pod name first
        stdout, stderr, code = self.kubectl("get pods -n default -o json")
        data = json.loads(stdout)
        pods = [p for p in data.get('items', []) if 'hello-mcp-server' in p['metadata']['name']]
        assert len(pods) > 0, "No hello-mcp-server pods found"
        pod_name = pods[0]['metadata']['name']
        stdout, stderr, code = self.kubectl(f"logs {pod_name} -n default --tail=10")
        assert "listener established" in stdout or "started bind" in stdout, \
            "MCP server not properly initialized"
    
    def test_agent_has_tools_configured(self):
        """Test if agents have tools properly configured"""
        stdout, stderr, code = self.kubectl("get agent hello-world-agent -o json")
        data = json.loads(stdout)
        tools = data['spec']['declarative'].get('tools', [])
        assert len(tools) > 0, "No tools configured"
        assert tools[0]['type'] == 'McpServer', "Tool type is not McpServer"
    
    def test_agent_references_correct_mcpserver(self):
        """Test if agent references the correct MCPServer"""
        stdout, stderr, code = self.kubectl("get agent hello-world-agent -o json")
        data = json.loads(stdout)
        mcp_server = data['spec']['declarative']['tools'][0]['mcpServer']
        assert mcp_server['kind'] == 'MCPServer', "Wrong kind"
        assert mcp_server['name'] == 'hello-mcp', "Wrong MCPServer name"
    
    def test_kagent_controller_running(self):
        """Test if kagent controller is running"""
        stdout, stderr, code = self.kubectl("get pods -n default -o json")
        data = json.loads(stdout)
        pods = [p for p in data.get('items', []) if 'kagent-controller' in p['metadata']['name']]
        assert len(pods) > 0, "No kagent-controller pods found"
        assert pods[0]['status']['phase'] == 'Running', "Controller not running"
    
    def test_kagent_ui_running(self):
        """Test if kagent UI is running"""
        stdout, stderr, code = self.kubectl("get pods -n default -o json")
        data = json.loads(stdout)
        pods = [p for p in data.get('items', []) if 'kagent-ui' in p['metadata']['name']]
        assert len(pods) > 0, "No kagent-ui pods found"
        assert pods[0]['status']['phase'] == 'Running', "UI not running"
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 KAGENT FRAMEWORK TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Total:  {self.results['passed'] + self.results['failed']}")
        
        if self.results['failed'] > 0:
            print("\n❌ Failed Tests:")
            for test in self.results['tests']:
                if test['status'] == 'FAILED':
                    print(f"   - {test['name']}")
                    if 'error' in test:
                        print(f"     Error: {test['error']}")
        
        print("\n" + "="*60)
        
        success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed'])) * 100
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED!")
        elif success_rate >= 80:
            print(f"⚠️  Most tests passed ({success_rate:.1f}%)")
        else:
            print(f"❌ Many tests failed ({success_rate:.1f}% passed)")
        
        return success_rate >= 80

def main():
    print("="*60)
    print("🚀 KAGENT FRAMEWORK COMPREHENSIVE TEST")
    print("="*60)
    
    tester = KagentTester()
    
    # Test MCPServers
    print("\n📦 Testing MCPServers...")
    tester.test("MCPServer hello-mcp exists", tester.test_mcpserver_hello_mcp_exists)
    tester.test("MCPServer hello-mcp is ready", tester.test_mcpserver_hello_mcp_ready)
    tester.test("MCPServer hello-mcp-server exists", tester.test_mcpserver_hello_mcp_server_exists)
    tester.test("MCPServer hello-mcp-server is ready", tester.test_mcpserver_hello_mcp_server_ready)
    tester.test("MCPServer pods are running", tester.test_mcpserver_pod_running)
    tester.test("MCP service exists", tester.test_mcp_service_exists)
    tester.test("MCP server logs show initialization", tester.test_mcp_server_logs)
    
    # Test Agents
    print("\n🤖 Testing Agents...")
    tester.test("Agent hello-world-agent exists", tester.test_agent_hello_world_exists)
    tester.test("Agent hello-mcp-agent exists", tester.test_agent_hello_mcp_exists)
    tester.test("Agent has tools configured", tester.test_agent_has_tools_configured)
    tester.test("Agent references correct MCPServer", tester.test_agent_references_correct_mcpserver)
    
    # Test Configuration
    print("\n⚙️  Testing Configuration...")
    tester.test("ModelConfig gemini-pro exists", tester.test_model_config_exists)
    tester.test("ConfigMap hello-mcp-tool exists", tester.test_configmap_hello_mcp_tool_exists)
    
    # Test Kagent Infrastructure
    print("\n🏗️  Testing Kagent Infrastructure...")
    tester.test("Kagent controller is running", tester.test_kagent_controller_running)
    tester.test("Kagent UI is running", tester.test_kagent_ui_running)
    
    # Print summary
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

