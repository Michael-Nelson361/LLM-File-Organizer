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
    
    def _generate_safe_filename(self, original_path: Path) -> Path:
        """Generate a safe filename that doesn't conflict with existing files."""
        parent = original_path.parent
        stem = original_path.stem
        suffix = original_path.suffix
        
        counter = 1
        while True:
            # Generate new filename: file (1).txt, file (2).txt, etc.
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Safety limit to prevent infinite loops
            if counter > 9999:
                # Use timestamp as last resort
                import time
                timestamp = int(time.time())
                new_name = f"{stem}_{timestamp}{suffix}"
                return parent / new_name
    
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
    
    def move_file(self, source: str, destination: str, auto_rename: bool = True) -> Dict[str, any]:
        try:
            src_path = self._safe_path(source)
            dst_path = self._safe_path(destination)
            
            if not src_path.exists():
                return {"error": f"Source does not exist: {source}"}
            
            if src_path.is_dir():
                return {"error": "Use move_directory for directories"}
            
            # CRITICAL SAFETY: Check for file conflicts before moving
            original_dst_path = dst_path
            if dst_path.exists():
                if not auto_rename:
                    return {"error": f"Destination file already exists: {destination}. File would be overwritten."}
                
                # Auto-generate safe filename to prevent overwrite
                dst_path = self._generate_safe_filename(dst_path)
                self.logger.warning(f"Destination exists, auto-renamed to: {dst_path.relative_to(self.root_path)}")
            
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform the move
            shutil.move(str(src_path), str(dst_path))
            
            # Log the operation with conflict resolution info
            if dst_path != original_dst_path:
                self.logger.info(f"Moved file with auto-rename: {source} -> {dst_path.relative_to(self.root_path)} (original destination existed)")
                return {"success": True, "message": f"Moved {source} to {dst_path.relative_to(self.root_path)} (renamed to avoid overwrite)", "renamed": True, "final_path": str(dst_path.relative_to(self.root_path))}
            else:
                self.logger.info(f"Moved file: {source} -> {destination}")
                return {"success": True, "message": f"Moved {source} to {destination}"}
            
        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {str(e)}")
            return {"error": f"Failed to move file: {str(e)}"}
    
    def move_directory(self, source: str, destination: str, auto_rename: bool = True) -> Dict[str, any]:
        try:
            src_path = self._safe_path(source)
            dst_path = self._safe_path(destination)
            
            if not src_path.exists():
                return {"error": f"Source does not exist: {source}"}
            
            if not src_path.is_dir():
                return {"error": "Use move_file for files"}
            
            # CRITICAL SAFETY: Check for directory conflicts before moving
            original_dst_path = dst_path
            if dst_path.exists():
                if not auto_rename:
                    return {"error": f"Destination directory already exists: {destination}. Directory would be merged or overwritten."}
                
                # Auto-generate safe directory name to prevent conflicts
                dst_path = self._generate_safe_filename(dst_path)
                self.logger.warning(f"Destination directory exists, auto-renamed to: {dst_path.relative_to(self.root_path)}")
            
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform the move
            shutil.move(str(src_path), str(dst_path))
            
            # Log the operation with conflict resolution info
            if dst_path != original_dst_path:
                self.logger.info(f"Moved directory with auto-rename: {source} -> {dst_path.relative_to(self.root_path)} (original destination existed)")
                return {"success": True, "message": f"Moved directory {source} to {dst_path.relative_to(self.root_path)} (renamed to avoid conflicts)", "renamed": True, "final_path": str(dst_path.relative_to(self.root_path))}
            else:
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
    
    def bulk_move_files(self, file_patterns: List[str], destination_dir: str, auto_rename: bool = True) -> Dict[str, any]:
        """Safely move multiple files matching patterns to a destination directory."""
        try:
            dst_dir_path = self._safe_path(destination_dir)
            
            # Create destination directory if it doesn't exist
            dst_dir_path.mkdir(parents=True, exist_ok=True)
            
            moved_files = []
            errors = []
            renamed_files = []
            
            for pattern in file_patterns:
                # Use glob to find matching files
                root_path_obj = Path(self.root_path)
                matching_files = list(root_path_obj.glob(pattern))
                
                for file_path in matching_files:
                    if file_path.is_file():
                        # Get relative path from root
                        relative_source = str(file_path.relative_to(self.root_path))
                        relative_dest = str(dst_dir_path / file_path.name)
                        
                        # Use the safe move_file method
                        result = self.move_file(relative_source, relative_dest, auto_rename)
                        
                        if result.get("success"):
                            if result.get("renamed"):
                                renamed_files.append({
                                    "original": relative_source,
                                    "intended": relative_dest,
                                    "actual": result.get("final_path")
                                })
                            else:
                                moved_files.append({
                                    "source": relative_source,
                                    "destination": relative_dest
                                })
                        else:
                            errors.append({
                                "file": relative_source,
                                "error": result.get("error")
                            })
            
            # Log summary
            self.logger.info(f"Bulk move completed: {len(moved_files)} moved, {len(renamed_files)} renamed, {len(errors)} errors")
            
            return {
                "success": True,
                "moved_files": moved_files,
                "renamed_files": renamed_files,
                "errors": errors,
                "summary": f"Moved {len(moved_files)} files, renamed {len(renamed_files)} to avoid conflicts, {len(errors)} errors"
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk move operation: {str(e)}")
            return {"error": f"Bulk move failed: {str(e)}"}
    
    def get_move_preview(self, source: str, destination: str) -> Dict[str, any]:
        """Preview what would happen during a move operation without actually moving."""
        try:
            src_path = self._safe_path(source)
            dst_path = self._safe_path(destination)
            
            if not src_path.exists():
                return {"error": f"Source does not exist: {source}"}
            
            preview = {
                "source": source,
                "destination": destination,
                "source_type": "directory" if src_path.is_dir() else "file",
                "will_create_dirs": not dst_path.parent.exists(),
                "conflict": dst_path.exists(),
                "safe": True
            }
            
            if preview["conflict"]:
                # Show what the auto-renamed version would be
                safe_path = self._generate_safe_filename(dst_path)
                preview["auto_rename_to"] = str(safe_path.relative_to(self.root_path))
                preview["conflict_type"] = "directory" if dst_path.is_dir() else "file"
            
            if preview["will_create_dirs"]:
                preview["dirs_to_create"] = str(dst_path.parent.relative_to(self.root_path))
            
            return preview
            
        except Exception as e:
            self.logger.error(f"Error generating move preview for {source} to {destination}: {str(e)}")
            return {"error": f"Failed to generate preview: {str(e)}"}