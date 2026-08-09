class AppState:
    def __init__(self):
        self.selected_folder = ""
        self.image_files = []
        self.original_files = []
        self.rotations = {}
        
        # Observers pattern
        self._observers = []
        
    def add_observer(self, observer_callback):
        """
        상태 변경을 감지할 옵저버 콜백 함수를 등록합니다.
        
        Args:
            observer_callback (callable): 상태 변경 시 호출될 함수
        """
        if observer_callback not in self._observers:
            self._observers.append(observer_callback)
            
    def notify_observers(self, *args, **kwargs):
        """
        등록된 모든 옵저버에게 이벤트 발생을 알립니다.
        
        Args:
            *args, **kwargs: 옵저버 콜백에 전달할 인자(주로 event 이름)
        """
        for callback in self._observers:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in observer: {e}")

    def update_files(self, folder, files):
        """
        선택된 폴더와 이미지 파일 목록을 새롭게 업데이트합니다.
        
        Args:
            folder (str): 선택된 폴더 경로
            files (list): 선택된 파일들의 리스트
        """
        self.selected_folder = folder
        self.image_files = files.copy() if files else []
        self.original_files = self.image_files.copy()
        self.rotations = {}
        self.notify_observers(event="files_updated")
        
    def get_rotation(self, filepath):
        """
        특정 파일의 현재 회전 각도를 가져옵니다.
        
        Args:
            filepath (str): 파일의 절대 경로
        Returns:
            int: 회전 각도 (기본 0도)
        """
        return self.rotations.get(filepath, 0)
        
    def set_rotation(self, filepath, rotation):
        """
        특정 파일의 회전 각도를 설정하고 옵저버에게 알립니다.
        
        Args:
            filepath (str): 파일의 절대 경로
            rotation (int): 적용할 회전 각도
        """
        self.rotations[filepath] = rotation
        self.notify_observers(event="rotation_updated", filepath=filepath)
        
    def remove_files(self, indices):
        """
        지정된 인덱스들의 파일을 목록에서 삭제합니다.
        인덱스 밀림을 방지하기 위해 역순으로 삭제를 진행합니다.
        
        Args:
            indices (list): 삭제할 파일의 인덱스 리스트
        """
        # Remove from highest index to lowest
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.image_files):
                del self.image_files[i]
        self.notify_observers(event="files_removed")
        
    def move_files_up(self, indices):
        """
        선택된 항목들을 리스트에서 한 칸 위로 이동시킵니다.
        
        Args:
            indices (list): 위로 이동할 파일의 인덱스 리스트
        """
        changed = False
        for i in indices:
            if i > 0 and (i-1) not in indices:
                self.image_files[i], self.image_files[i-1] = self.image_files[i-1], self.image_files[i]
                changed = True
        if changed:
            self.notify_observers(event="files_reordered")
            
    def move_files_down(self, indices):
        """
        선택된 항목들을 리스트에서 한 칸 아래로 이동시킵니다.
        
        Args:
            indices (list): 아래로 이동할 파일의 인덱스 리스트
        """
        changed = False
        max_idx = len(self.image_files) - 1
        for i in reversed(indices):
            if i < max_idx and (i+1) not in indices:
                self.image_files[i], self.image_files[i+1] = self.image_files[i+1], self.image_files[i]
                changed = True
        if changed:
            self.notify_observers(event="files_reordered")

    def move_files_to(self, indices, target_index):
        """
        드래그 앤 드롭 등으로 여러 파일을 특정 위치로 이동시킵니다.
        
        Args:
            indices (list): 이동시킬 파일들의 원본 인덱스 리스트
            target_index (int): 삽입될 목표 인덱스
        """
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
