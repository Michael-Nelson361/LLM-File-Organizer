import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging

class SafeFilesystemOperations:
    def __init__(self, root_path: str, logger: logging.Logger):
        self.root_path = Path(root_path).resolve()
        self.logger = logger
        
        if not self.root_path.exists():
            raise ValueError(f"Root path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Root path is not a directory: {self.root_path}")
    
    def _validate_path(self, path: Path) -> bool:
        try:
            resolved_path = path.resolve()
            return resolved_path.is_relative_to(self.root_path)
        except (OSError, ValueError):
            return False
    
    def _safe_path(self, path_str: str) -> Path:
        path = Path(path_str)
        if path.is_absolute():
            full_path = path
        else:
            full_path = self.root_path / path
        
        full_path = full_path.resolve()
        
        if not self._validate_path(full_path):
            raise ValueError(f"Path outside allowed directory: {path_str}")
        
        return full_path
    
    def list_directory(self, path: str = "") -> Dict[str, any]:
        target_path = self._safe_path(path)
        
        if not target_path.exists():
            return {"error": f"Path does not exist: {path}"}
        
        if not target_path.is_dir():
            return {"error": f"Path is not a directory: {path}"}
        
        try:
            items = []
            for item in target_path.iterdir():
                relative_path = item.relative_to(self.root_path)
                items.append({
                    "name": item.name,
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            self.logger.info(f"Listed directory: {path}")
            return {"items": items}
        except Exception as e:
            self.logger.error(f"Error listing directory {path}: {str(e)}")
            return {"error": f"Failed to list directory: {str(e)}"}
    
    def move_file(self, source: str, destination: str) -> Dict[str, any]:
        try:
            src_path = self._safe_path(source)
            dst_path = self._safe_path(destination)
            
            if not src_path.exists():
                return {"error": f"Source does not exist: {source}"}
            
            if src_path.is_dir():
                return {"error": "Use move_directory for directories"}
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            self.logger.info(f"Moved file: {source} -> {destination}")
            return {"success": True, "message": f"Moved {source} to {destination}"}
            
        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {str(e)}")
            return {"error": f"Failed to move file: {str(e)}"}
    
    def move_directory(self, source: str, destination: str) -> Dict[str, any]:
        try:
            src_path = self._safe_path(source)
            dst_path = self._safe_path(destination)
            
            if not src_path.exists():
                return {"error": f"Source does not exist: {source}"}
            
            if not src_path.is_dir():
                return {"error": "Use move_file for files"}
            
            if dst_path.exists():
                return {"error": f"Destination already exists: {destination}"}
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            self.logger.info(f"Moved directory: {source} -> {destination}")
            return {"success": True, "message": f"Moved directory {source} to {destination}"}
            
        except Exception as e:
            self.logger.error(f"Error moving directory {source} to {destination}: {str(e)}")
            return {"error": f"Failed to move directory: {str(e)}"}
    
    def rename_file(self, old_name: str, new_name: str) -> Dict[str, any]:
        try:
            old_path = self._safe_path(old_name)
            new_path = self._safe_path(new_name)
            
            if not old_path.exists():
                return {"error": f"File does not exist: {old_name}"}
            
            if new_path.exists():
                return {"error": f"Target name already exists: {new_name}"}
            
            old_path.rename(new_path)
            self.logger.info(f"Renamed: {old_name} -> {new_name}")
            return {"success": True, "message": f"Renamed {old_name} to {new_name}"}
            
        except Exception as e:
            self.logger.error(f"Error renaming {old_name} to {new_name}: {str(e)}")
            return {"error": f"Failed to rename: {str(e)}"}
    
    def create_directory(self, path: str) -> Dict[str, any]:
        try:
            target_path = self._safe_path(path)
            
            if target_path.exists():
                return {"error": f"Directory already exists: {path}"}
            
            target_path.mkdir(parents=True, exist_ok=False)
            self.logger.info(f"Created directory: {path}")
            return {"success": True, "message": f"Created directory {path}"}
            
        except Exception as e:
            self.logger.error(f"Error creating directory {path}: {str(e)}")
            return {"error": f"Failed to create directory: {str(e)}"}
    
    def remove_empty_directory(self, path: str) -> Dict[str, any]:
        try:
            target_path = self._safe_path(path)
            
            if not target_path.exists():
                return {"error": f"Directory does not exist: {path}"}
            
            if not target_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            if any(target_path.iterdir()):
                return {"error": f"Directory is not empty: {path}"}
            
            target_path.rmdir()
            self.logger.info(f"Removed empty directory: {path}")
            return {"success": True, "message": f"Removed empty directory {path}"}
            
        except Exception as e:
            self.logger.error(f"Error removing directory {path}: {str(e)}")
            return {"error": f"Failed to remove directory: {str(e)}"}
    
    def get_file_info(self, path: str) -> Dict[str, any]:
        try:
            target_path = self._safe_path(path)
            
            if not target_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            stat = target_path.stat()
            relative_path = target_path.relative_to(self.root_path)
            
            info = {
                "name": target_path.name,
                "path": str(relative_path),
                "type": "directory" if target_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime
            }
            
            if target_path.is_dir():
                try:
                    info["contents_count"] = len(list(target_path.iterdir()))
                except PermissionError:
                    info["contents_count"] = "Permission denied"
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {path}: {str(e)}")
            return {"error": f"Failed to get file info: {str(e)}"}