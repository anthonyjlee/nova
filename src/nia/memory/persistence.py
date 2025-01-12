"""
Persistence layer for memory system.
"""

import logging
import asyncio
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
from .memory_types import AgentResponse, Analysis

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory persistence with command execution and task collections."""
    
    def __init__(self, working_dir: str = "/Users/alee5331/Documents/Projects/NIA"):
        """Initialize memory store."""
        self.working_dir = working_dir
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.collections = {
            "task_updates": {
                "vectors_config": {
                    "size": 384,
                    "distance": "Cosine"
                },
                "indexes": [
                    {"field_name": "task_id", "field_schema": "keyword"},
                    {"field_name": "status", "field_schema": "keyword"},
                    {"field_name": "domain", "field_schema": "keyword"},
                    {"field_name": "timestamp", "field_schema": "datetime"}
                ]
            }
        }
    
    async def setup_collections(self):
        """Set up required collections and indexes."""
        try:
            for collection_name, config in self.collections.items():
                # Create collection if it doesn't exist
                try:
                    await self.create_collection(
                        name=collection_name,
                        vectors_config=config["vectors_config"]
                    )
                except Exception as e:
                    if "already exists" not in str(e):
                        raise

                # Create indexes
                for index in config["indexes"]:
                    try:
                        await self.create_payload_index(
                            collection_name=collection_name,
                            field_name=index["field_name"],
                            field_schema=index["field_schema"]
                        )
                    except Exception as e:
                        if "already exists" not in str(e):
                            raise

            logger.info("Collections and indexes set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set up collections: {str(e)}")
            return False

    async def execute_command(
        self,
        command: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Execute a system command."""
        try:
            # Format command context
            command_context = {
                'command': command,
                'working_dir': self.working_dir,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.working_dir
            )
            
            # Store active process
            process_id = f"process_{datetime.now().isoformat()}"
            self.active_processes[process_id] = process
            
            # Wait for output
            stdout, stderr = await process.communicate()
            
            # Remove from active processes
            del self.active_processes[process_id]
            
            # Check result
            if process.returncode == 0:
                return AgentResponse(
                    response=f"Command executed successfully: {command}",
                    analysis=Analysis(
                        key_points=[
                            "Command successful",
                            f"Output: {stdout.decode() if stdout else 'No output'}"
                        ],
                        confidence=1.0,
                        state_update="command execution complete"
                    )
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return AgentResponse(
                    response=f"Command failed: {error_msg}",
                    analysis=Analysis(
                        key_points=[
                            "Command failed",
                            f"Error: {error_msg}"
                        ],
                        confidence=0.1,
                        state_update="command execution failed"
                    )
                )
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return AgentResponse(
                response=f"Error executing command: {str(e)}",
                analysis=Analysis(
                    key_points=[
                        "Execution error",
                        str(e)
                    ],
                    confidence=0.1,
                    state_update="command execution error"
                )
            )
    
    async def validate_command(
        self,
        command: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate a command before execution."""
        # Check for dangerous commands
        dangerous_commands = [
            'rm -rf',
            'sudo',
            'chmod',
            'chown',
            'mkfs',
            'dd',
            'mv /',
            'cp /',
            '> /',
            '>> /'
        ]
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                return False, f"Command contains dangerous operation: {dangerous}"
        
        # Check working directory
        if '..' in command or '~' in command:
            return False, "Command contains relative path navigation"
        
        # Check for web access
        if any(cmd in command for cmd in ['curl', 'wget', 'nc']):
            if 'localhost' not in command and '127.0.0.1' not in command:
                return False, "Command attempts external web access"
        
        # Check for file operations
        if any(cmd in command for cmd in ['>', '>>', 'tee']):
            target = command.split('>')[-1].strip().split()[0]
            target_path = Path(target)
            if not target_path.is_relative_to(self.working_dir):
                return False, "Command attempts to write outside working directory"
        
        return True, "Command validated"
    
    def get_active_processes(self) -> List[Dict[str, Any]]:
        """Get list of active processes."""
        return [
            {
                'id': pid,
                'command': str(process.args),
                'status': 'running'
            }
            for pid, process in self.active_processes.items()
        ]
    
    async def cleanup(self) -> None:
        """Clean up active processes."""
        for process in self.active_processes.values():
            try:
                process.terminate()
                await asyncio.sleep(0.1)
                if process.poll() is None:
                    process.kill()
            except Exception as e:
                logger.error(f"Error cleaning up process: {str(e)}")
        
        self.active_processes.clear()
