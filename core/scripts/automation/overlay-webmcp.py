#!/usr/bin/env python3
"""
Overlay WebMCP Client
Model Context Protocol client for overlay management and discovery
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverlayAction(Enum):
    LIST = "list"
    CREATE = "create"
    VALIDATE = "validate"
    TEST = "test"
    BUILD = "build"
    APPLY = "apply"
    SEARCH = "search"
    GET_METADATA = "get_metadata"

@dataclass
class OverlayRequest:
    action: OverlayAction
    parameters: Dict[str, Any]
    overlay_path: Optional[str] = None

@dataclass
class OverlayResponse:
    success: bool
    data: Any
    error: Optional[str] = None
    warnings: List[str] = None

class OverlayWebMCPClient:
    def __init__(self, overlays_dir: str = "overlays"):
        self.overlays_dir = Path(overlays_dir)
        self.registry_dir = self.overlays_dir / "registry"
        
    async def handle_request(self, request: OverlayRequest) -> OverlayResponse:
        """Handle MCP request for overlay operations"""
        try:
            if request.action == OverlayAction.LIST:
                return await self._list_overlays(request.parameters)
            elif request.action == OverlayAction.CREATE:
                return await self._create_overlay(request.parameters)
            elif request.action == OverlayAction.VALIDATE:
                return await self._validate_overlay(request.overlay_path, request.parameters)
            elif request.action == OverlayAction.TEST:
                return await self._test_overlay(request.overlay_path, request.parameters)
            elif request.action == OverlayAction.BUILD:
                return await self._build_overlay(request.overlay_path, request.parameters)
            elif request.action == OverlayAction.APPLY:
                return await self._apply_overlay(request.overlay_path, request.parameters)
            elif request.action == OverlayAction.SEARCH:
                return await self._search_overlays(request.parameters)
            elif request.action == OverlayAction.GET_METADATA:
                return await self._get_metadata(request.overlay_path, request.parameters)
            else:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error=f"Unknown action: {request.action}"
                )
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return OverlayResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _list_overlays(self, params: Dict[str, Any]) -> OverlayResponse:
        """List available overlays"""
        try:
            category = params.get('category')
            format_type = params.get('format', 'table')
            
            catalog_path = self.registry_dir / "catalog.yaml"
            if not catalog_path.exists():
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Catalog not found"
                )
            
            with open(catalog_path, 'r') as f:
                catalog = yaml.safe_load(f)
            
            overlays = catalog.get('overlays', [])
            
            if category:
                overlays = [o for o in overlays if o.get('category') == category]
            
            if format_type == 'json':
                data = overlays
            else:
                data = self._format_overlays_table(overlays)
            
            return OverlayResponse(success=True, data=data)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _create_overlay(self, params: Dict[str, Any]) -> OverlayResponse:
        """Create a new overlay"""
        try:
            name = params.get('name')
            category = params.get('category')
            base_path = params.get('base_path')
            template = params.get('template')
            
            if not all([name, category, base_path]):
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Missing required parameters: name, category, base_path"
                )
            
            # Import CLI for overlay creation
            import subprocess
            import sys
            
            cli_script = Path(__file__).parent / 'overlay-cli.py'
            
            cmd = [
                sys.executable, str(cli_script), 'create',
                name, category, base_path
            ]
            
            if template:
                cmd.extend(['--template', template])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return OverlayResponse(
                    success=True,
                    data={"message": f"Overlay {name} created successfully", "path": f"core/deployment/overlays/{category}/{name}"}
                )
            else:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error=result.stderr
                )
                
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _validate_overlay(self, overlay_path: str, params: Dict[str, Any]) -> OverlayResponse:
        """Validate an overlay"""
        try:
            if not overlay_path:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Overlay path is required"
                )
            
            import subprocess
            import sys
            
            validation_script = Path(__file__).parent / 'validate-overlays.py'
            
            result = subprocess.run([
                sys.executable, str(validation_script), overlay_path
            ], capture_output=True, text=True)
            
            success = result.returncode == 0
            data = {
                "output": result.stdout,
                "errors": result.stderr if result.returncode != 0 else None
            }
            
            return OverlayResponse(success=success, data=data)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _test_overlay(self, overlay_path: str, params: Dict[str, Any]) -> OverlayResponse:
        """Test an overlay"""
        try:
            if not overlay_path:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Overlay path is required"
                )
            
            import subprocess
            import sys
            
            test_script = Path(__file__).parent / 'test-overlays.py'
            
            result = subprocess.run([
                sys.executable, str(test_script), overlay_path
            ], capture_output=True, text=True)
            
            success = result.returncode == 0
            data = {
                "output": result.stdout,
                "errors": result.stderr if result.returncode != 0 else None
            }
            
            return OverlayResponse(success=success, data=data)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _build_overlay(self, overlay_path: str, params: Dict[str, Any]) -> OverlayResponse:
        """Build an overlay"""
        try:
            if not overlay_path:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Overlay path is required"
                )
            
            import subprocess
            
            result = subprocess.run([
                'kustomize', 'build', overlay_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return OverlayResponse(
                    success=True,
                    data={"manifest": result.stdout}
                )
            else:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error=result.stderr
                )
                
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _apply_overlay(self, overlay_path: str, params: Dict[str, Any]) -> OverlayResponse:
        """Apply an overlay"""
        try:
            if not overlay_path:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Overlay path is required"
                )
            
            dry_run = params.get('dry_run', False)
            
            import subprocess
            
            # Build overlay first
            build_result = subprocess.run([
                'kustomize', 'build', overlay_path
            ], capture_output=True, text=True)
            
            if build_result.returncode != 0:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Build failed: " + build_result.stderr
                )
            
            # Apply with kubectl
            cmd = ['kubectl', 'apply']
            if dry_run:
                cmd.extend(['--dry-run=client'])
            cmd.extend(['-f', '-'])
            
            apply_result = subprocess.run(
                cmd,
                input=build_result.stdout,
                capture_output=True,
                text=True
            )
            
            success = apply_result.returncode == 0
            data = {
                "output": apply_result.stdout,
                "dry_run": dry_run
            }
            
            if not success:
                data["error"] = apply_result.stderr
            
            return OverlayResponse(success=success, data=data)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _search_overlays(self, params: Dict[str, Any]) -> OverlayResponse:
        """Search overlays"""
        try:
            query = params.get('query', '')
            tags = params.get('tags', [])
            category = params.get('category')
            
            catalog_path = self.registry_dir / "catalog.yaml"
            if not catalog_path.exists():
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Catalog not found"
                )
            
            with open(catalog_path, 'r') as f:
                catalog = yaml.safe_load(f)
            
            overlays = catalog.get('overlays', [])
            results = []
            
            for overlay in overlays:
                match = True
                
                # Query search
                if query and query.lower() not in overlay.get('name', '').lower() and \
                   query.lower() not in overlay.get('description', '').lower():
                    match = False
                
                # Category filter
                if category and overlay.get('category') != category:
                    match = False
                
                # Tags filter
                if tags and not any(tag in overlay.get('tags', []) for tag in tags):
                    match = False
                
                if match:
                    results.append(overlay)
            
            return OverlayResponse(success=True, data=results)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    async def _get_metadata(self, overlay_path: str, params: Dict[str, Any]) -> OverlayResponse:
        """Get overlay metadata"""
        try:
            if not overlay_path:
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Overlay path is required"
                )
            
            overlay_dir = Path(overlay_path)
            metadata_file = overlay_dir / "overlay-metadata.yaml"
            
            if not metadata_file.exists():
                return OverlayResponse(
                    success=False,
                    data=None,
                    error="Metadata file not found"
                )
            
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)
            
            return OverlayResponse(success=True, data=metadata)
            
        except Exception as e:
            return OverlayResponse(success=False, data=None, error=str(e))
    
    def _format_overlays_table(self, overlays: List[Dict[str, Any]]) -> str:
        """Format overlays as table"""
        if not overlays:
            return "No overlays found"
        
        # Simple table formatting
        headers = ["Name", "Category", "Version", "Description"]
        rows = []
        
        for overlay in overlays:
            rows.append([
                overlay.get('name', 'N/A'),
                overlay.get('category', 'N/A'),
                overlay.get('version', 'N/A'),
                overlay.get('description', 'N/A')[:50] + '...' if len(overlay.get('description', '')) > 50 else overlay.get('description', 'N/A')
            ])
        
        # Build table string
        table = " | ".join(headers) + "\n"
        table += "-" * (len(headers[0]) + len(headers[1]) + len(headers[2]) + len(headers[3]) + 15) + "\n"
        
        for row in rows:
            table += " | ".join(row) + "\n"
        
        return table

# MCP Server implementation
class OverlayMCPServer:
    def __init__(self, overlays_dir: str = "overlays"):
        self.client = OverlayWebMCPClient(overlays_dir)
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol request"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            
            if method == 'core/deployment/overlays/list':
                overlay_request = OverlayRequest(OverlayAction.LIST, params)
            elif method == 'core/deployment/overlays/create':
                overlay_request = OverlayRequest(OverlayAction.CREATE, params)
            elif method == 'core/deployment/overlays/validate':
                overlay_path = params.get('overlay_path')
                overlay_request = OverlayRequest(OverlayAction.VALIDATE, params, overlay_path)
            elif method == 'core/deployment/overlays/test':
                overlay_path = params.get('overlay_path')
                overlay_request = OverlayRequest(OverlayAction.TEST, params, overlay_path)
            elif method == 'core/deployment/overlays/build':
                overlay_path = params.get('overlay_path')
                overlay_request = OverlayRequest(OverlayAction.BUILD, params, overlay_path)
            elif method == 'core/deployment/overlays/apply':
                overlay_path = params.get('overlay_path')
                overlay_request = OverlayRequest(OverlayAction.APPLY, params, overlay_path)
            elif method == 'core/deployment/overlays/search':
                overlay_request = OverlayRequest(OverlayAction.SEARCH, params)
            elif method == 'core/deployment/overlays/get_metadata':
                overlay_path = params.get('overlay_path')
                overlay_request = OverlayRequest(OverlayAction.GET_METADATA, params, overlay_path)
            else:
                return {
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
            
            response = await self.client.handle_request(overlay_request)
            
            if response.success:
                return {
                    'result': response.data,
                    'warnings': response.warnings or []
                }
            else:
                return {
                    'error': {
                        'code': -32000,
                        'message': response.error
                    }
                }
                
        except Exception as e:
            logger.error(f"MCP request error: {e}")
            return {
                'error': {
                    'code': -32000,
                    'message': str(e)
                }
            }

# CLI interface for MCP server
async def main():
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Overlay WebMCP Server')
    parser.add_argument('--overlays-dir', default='overlays', help='Overlays directory')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--host', default='localhost', help='Server host')
    
    args = parser.parse_args()
    
    server = OverlayMCPServer(args.overlays_dir)
    
    # Simple HTTP server for MCP (in a real implementation, use proper MCP server)
    from aiohttp import web
    
    async def handle_http_request(request):
        try:
            mcp_request = await request.json()
            mcp_response = await server.handle_mcp_request(mcp_request)
            return web.json_response(mcp_response)
        except Exception as e:
            return web.json_response({
                'error': {
                    'code': -32000,
                    'message': str(e)
                }
            })
    
    app = web.Application()
    app.router.add_post('/mcp', handle_http_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    
    logger.info(f"Overlay MCP server running on http://{args.host}:{args.port}")
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down server")

if __name__ == '__main__':
    asyncio.run(main())
