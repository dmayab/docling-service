import asyncio
import time
from typing import Dict, Any, Optional

class TaskCleanupManager:
    """
    Gestor de limpieza retardada de tareas completadas
    Mantiene las tareas en memoria por un tiempo después de completarse
    para que el frontend tenga tiempo de consultarlas
    """
    
    def __init__(self, cleanup_delay_seconds: int = 300):  # 5 minutos por defecto
        self.cleanup_delay = cleanup_delay_seconds
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        
    def mark_for_cleanup(self, task_id: str, task_data: Dict[str, Any]):
        """Marca una tarea completada para limpieza futura"""
        self.completed_tasks[task_id] = {
            'data': task_data,
            'completed_at': time.time()
        }
        
    def cleanup_old_tasks(self):
        """Limpia tareas que han superado el tiempo de retención"""
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task_info in self.completed_tasks.items():
            if current_time - task_info['completed_at'] > self.cleanup_delay:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.completed_tasks[task_id]
            
        return len(tasks_to_remove)
        
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una tarea completada si todavía está disponible"""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]['data']
        return None
        
    async def start_cleanup_worker(self):
        """Worker en background que limpia tareas viejas cada minuto"""
        while True:
            try:
                cleaned = self.cleanup_old_tasks()
                if cleaned > 0:
                    print(f"🧹 Limpiadas {cleaned} tareas viejas del cache")
                await asyncio.sleep(60)  # Limpiar cada minuto
            except Exception as e:
                print(f"❌ Error en cleanup worker: {e}")
                await asyncio.sleep(60)

# Instancia global
task_cleanup_manager = TaskCleanupManager()