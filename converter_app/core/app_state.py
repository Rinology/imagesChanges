class AppState:
    def __init__(self):
        self.selected_folder = ""
        self.image_files = []
        self.original_files = []
        self.rotations = {}
        
        # Observers pattern
        self._observers = []
        
    def add_observer(self, observer_callback):
        if observer_callback not in self._observers:
            self._observers.append(observer_callback)
            
    def notify_observers(self, *args, **kwargs):
        for callback in self._observers:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in observer: {e}")

    def update_files(self, folder, files):
        self.selected_folder = folder
        self.image_files = files.copy() if files else []
        self.original_files = self.image_files.copy()
        self.rotations = {}
        self.notify_observers(event="files_updated")
        
    def get_rotation(self, filepath):
        return self.rotations.get(filepath, 0)
        
    def set_rotation(self, filepath, rotation):
        self.rotations[filepath] = rotation
        self.notify_observers(event="rotation_updated", filepath=filepath)
        
    def remove_files(self, indices):
        # Remove from highest index to lowest
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.image_files):
                del self.image_files[i]
        self.notify_observers(event="files_removed")
        
    def move_files_up(self, indices):
        changed = False
        for i in indices:
            if i > 0 and (i-1) not in indices:
                self.image_files[i], self.image_files[i-1] = self.image_files[i-1], self.image_files[i]
                changed = True
        if changed:
            self.notify_observers(event="files_reordered")
            
    def move_files_down(self, indices):
        changed = False
        max_idx = len(self.image_files) - 1
        for i in reversed(indices):
            if i < max_idx and (i+1) not in indices:
                self.image_files[i], self.image_files[i+1] = self.image_files[i+1], self.image_files[i]
                changed = True
        if changed:
            self.notify_observers(event="files_reordered")

    def move_files_to(self, indices, target_index):
        if not indices:
            return
        
        # Determine the insertion point after items are removed
        # Filter out the items being moved
        items_to_move = [self.image_files[i] for i in indices]
        new_files = [f for i, f in enumerate(self.image_files) if i not in indices]
        
        # We need to adjust target_index because the items have been removed
        # target_index is the original index before removal
        adjusted_target = target_index
        for i in indices:
            if i < target_index:
                adjusted_target -= 1
                
        # Insert the items at the adjusted target index
        new_files[adjusted_target:adjusted_target] = items_to_move
        self.image_files = new_files
        self.notify_observers(event="files_reordered")
