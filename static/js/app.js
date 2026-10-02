/**
 * Index Application Controller
 * Handles SPA state, interactions, drag-and-drop ingestion,
 * natural-language AI search, and per-file chat inquiries.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- State ---
  const state = {
    files: [],
    folders: [],
    tags: [],
    currentFilter: { type: 'all', value: null }, // 'all' | 'folder' | 'uncategorized' | 'tag'
    searchMode: 'ask', // 'ask' | 'filter'
    searchQuery: '',
    sortBy: 'newest',
    activeFileId: null,
    activeFile: null,
    activeTab: 'dossier',
    isSearching: false
  };

  // --- DOM Elements ---
  const elements = {
    // Header & Search
    sidebarToggleBtn: document.getElementById('sidebarToggleBtn'),
    sidebar: document.getElementById('sidebar'),
    themeToggleBtn: document.getElementById('themeToggleBtn'),
    headerUploadBtn: document.getElementById('headerUploadBtn'),
    aiStatusBadge: document.getElementById('aiStatusBadge'),
    aiStatusText: document.getElementById('aiStatusText'),
    searchModeAsk: document.getElementById('searchModeAsk'),
    searchModeFilter: document.getElementById('searchModeFilter'),
    searchInput: document.getElementById('searchInput'),
    searchClearBtn: document.getElementById('searchClearBtn'),
    searchSubmitBtn: document.getElementById('searchSubmitBtn'),
    
    // Sidebar
    folderList: document.getElementById('folderList'),
    tagCloud: document.getElementById('tagCloud'),
    newFolderBtn: document.getElementById('newFolderBtn'),
    clearTagFilterBtn: document.getElementById('clearTagFilterBtn'),
    totalFilesBadge: document.getElementById('totalFilesBadge'),
    uncategorizedBadge: document.getElementById('uncategorizedBadge'),
    storageUsageText: document.getElementById('storageUsageText'),
    
    // Main Catalog Area
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('fileInput'),
    uploadProgress: document.getElementById('uploadProgress'),
    searchBanner: document.getElementById('searchBanner'),
    bannerHeading: document.getElementById('bannerHeading'),
    bannerExplanation: document.getElementById('bannerExplanation'),
    clearSearchBannerBtn: document.getElementById('clearSearchBannerBtn'),
    currentViewName: document.getElementById('currentViewName'),
    resultCountPill: document.getElementById('resultCountPill'),
    sortBySelect: document.getElementById('sortBySelect'),
    fileGrid: document.getElementById('fileGrid'),
    emptyState: document.getElementById('emptyState'),
    emptyUploadBtn: document.getElementById('emptyUploadBtn'),
    
    // Slide-over Inspector Drawer
    inspectorBackdrop: document.getElementById('inspectorBackdrop'),
    inspectorDrawer: document.getElementById('inspectorDrawer'),
    drawerCloseBtn: document.getElementById('drawerCloseBtn'),
    drawerFileName: document.getElementById('drawerFileName'),
    drawerFileExt: document.getElementById('drawerFileExt'),
    drawerDownloadBtn: document.getElementById('drawerDownloadBtn'),
    drawerDeleteBtn: document.getElementById('drawerDeleteBtn'),
    tabDossierBtn: document.getElementById('tabDossierBtn'),
    tabChatBtn: document.getElementById('tabChatBtn'),
    tabDossier: document.getElementById('tabDossier'),
    tabChat: document.getElementById('tabChat'),
    
    // Dossier Tab Elements
    drawerSummary: document.getElementById('drawerSummary'),
    reprocessAiBtn: document.getElementById('reprocessAiBtn'),
    drawerTagList: document.getElementById('drawerTagList'),
    addTagForm: document.getElementById('addTagForm'),
    newTagInput: document.getElementById('newTagInput'),
    drawerFolderSelect: document.getElementById('drawerFolderSelect'),
    drawerFileSize: document.getElementById('drawerFileSize'),
    drawerMime: document.getElementById('drawerMime'),
    drawerDate: document.getElementById('drawerDate'),
    drawerPath: document.getElementById('drawerPath'),
    drawerTextPreview: document.getElementById('drawerTextPreview'),
    copyExtractedBtn: document.getElementById('copyExtractedBtn'),
    
    // Chat Tab Elements
    chatMessageLog: document.getElementById('chatMessageLog'),
    chatForm: document.getElementById('chatForm'),
    chatInputText: document.getElementById('chatInputText'),
    clearChatHistoryBtn: document.getElementById('clearChatHistoryBtn'),
    starterChips: document.querySelectorAll('.chip-btn'),
    
    // Folder Modal
    newFolderModal: document.getElementById('newFolderModal'),
    closeFolderModalBtn: document.getElementById('closeFolderModalBtn'),
    cancelFolderModalBtn: document.getElementById('cancelFolderModalBtn'),
    createFolderForm: document.getElementById('createFolderForm'),
    folderNameInput: document.getElementById('folderNameInput'),
    folderDescInput: document.getElementById('folderDescInput'),
    
    // Toast Container
    toastContainer: document.getElementById('toastContainer')
  };

  // --- Initialize Application ---
  initTheme();
  setupEventListeners();
  loadInitialData();

  // ============================================================================
  // THEME MANAGEMENT
  // ============================================================================
  function initTheme() {
    const savedTheme = localStorage.getItem('index_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('index_theme', newTheme);
    updateThemeIcon(newTheme);
  }

  function updateThemeIcon(theme) {
    elements.themeToggleBtn.innerHTML = theme === 'dark' 
      ? '<i class="fa-solid fa-sun"></i>' 
      : '<i class="fa-solid fa-moon"></i>';
  }

  // ============================================================================
  // EVENT LISTENERS SETUP
  // ============================================================================
  function setupEventListeners() {
    // Theme toggle
    elements.themeToggleBtn.addEventListener('click', toggleTheme);

    // Mobile sidebar toggle
    elements.sidebarToggleBtn.addEventListener('click', () => {
      elements.sidebar.classList.toggle('open');
    });

    // Navigation item clicks (All / Uncategorized)
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const filterType = item.dataset.filter;
        setNavFilter(filterType);
        if (window.innerWidth <= 960) elements.sidebar.classList.remove('open');
      });
    });

    // Clear tag filter button
    elements.clearTagFilterBtn.addEventListener('click', () => {
      setNavFilter('all');
    });

    // Sort order dropdown
    elements.sortBySelect.addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      fetchAndRenderFiles();
    });

    // File Ingestion Dropzone
    elements.dropzone.addEventListener('click', (e) => {
      if (e.target.closest('.format-chips')) return;
      elements.fileInput.click();
    });

    elements.headerUploadBtn.addEventListener('click', () => elements.fileInput.click());
    elements.emptyUploadBtn.addEventListener('click', () => elements.fileInput.click());

    elements.dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      elements.dropzone.classList.add('dragover');
    });

    elements.dropzone.addEventListener('dragleave', () => {
      elements.dropzone.classList.remove('dragover');
    });

    elements.dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      elements.dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files);
      }
    });

    elements.fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileUpload(e.target.files);
      }
    });

    // Search Mode Toggle
    elements.searchModeAsk.addEventListener('click', () => setSearchMode('ask'));
    elements.searchModeFilter.addEventListener('click', () => setSearchMode('filter'));

    // Search input & submission
    elements.searchInput.addEventListener('input', (e) => {
      const val = e.target.value;
      elements.searchClearBtn.classList.toggle('hidden', !val);
      if (state.searchMode === 'filter') {
        state.searchQuery = val.trim();
        fetchAndRenderFiles();
      }
    });

    elements.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        performSearch();
      }
    });

    elements.searchSubmitBtn.addEventListener('click', performSearch);
    elements.searchClearBtn.addEventListener('click', resetSearch);
    elements.clearSearchBannerBtn.addEventListener('click', resetSearch);

    // Inspector Drawer tabs & close
    elements.drawerCloseBtn.addEventListener('click', closeInspector);
    elements.inspectorBackdrop.addEventListener('click', closeInspector);

    elements.tabDossierBtn.addEventListener('click', () => switchDrawerTab('dossier'));
    elements.tabChatBtn.addEventListener('click', () => switchDrawerTab('chat'));

    // Reprocess AI button
    elements.reprocessAiBtn.addEventListener('click', handleReprocessAi);

    // Add manual tag
    elements.addTagForm.addEventListener('submit', handleAddTag);

    // Move folder assignment from drawer
    elements.drawerFolderSelect.addEventListener('change', handleFolderAssignment);

    // Copy extracted text
    elements.copyExtractedBtn.addEventListener('click', copyExtractedText);

    // Delete file from drawer
    elements.drawerDeleteBtn.addEventListener('click', () => {
      if (state.activeFileId) handleDeleteFile(state.activeFileId);
    });

    // Chat Form Submission
    elements.chatForm.addEventListener('submit', handleChatSubmit);
    elements.chatInputText.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        elements.chatForm.dispatchEvent(new Event('submit'));
      }
    });

    // Clear Chat History
    elements.clearChatHistoryBtn.addEventListener('click', handleClearChatHistory);

    // Starter Prompt Chips
    elements.starterChips.forEach(chip => {
      chip.addEventListener('click', () => {
        elements.chatInputText.value = chip.dataset.query;
        elements.chatInputText.focus();
      });
    });

    // Folder Modal
    elements.newFolderBtn.addEventListener('click', () => openFolderModal());
    elements.closeFolderModalBtn.addEventListener('click', () => closeFolderModal());
    elements.cancelFolderModalBtn.addEventListener('click', () => closeFolderModal());
    elements.createFolderForm.addEventListener('submit', handleCreateFolder);
  }

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  async function loadInitialData() {
    try {
      await Promise.all([
        fetchSystemStatus(),
        fetchFolders(),
        fetchTags()
      ]);
      await fetchAndRenderFiles();
    } catch (err) {
      showToast('Error loading archival catalog: ' + err.message, 'error');
    }
  }

  async function fetchSystemStatus() {
    try {
      const status = await API.getSystemStatus();
      if (status.ai.is_offline_fallback) {
        elements.aiStatusText.textContent = 'Offline Heuristic';
        elements.aiStatusBadge.title = 'Add GEMINI_API_KEY to .env for live Gemini model';
      } else {
        elements.aiStatusText.textContent = `Gemini (${status.ai.gemini_model})`;
        elements.aiStatusBadge.title = 'Connected to Google Gemini LLM';
      }
      if (status.stats) {
        elements.storageUsageText.textContent = formatBytes(status.stats.total_storage_bytes) + ' archived';
      }
    } catch (e) {
      elements.aiStatusText.textContent = 'Local Standby';
    }
  }

  async function fetchFolders() {
    try {
      const folders = await API.getFolders();
      state.folders = folders;
      renderFolders();
      populateFolderDropdowns();
    } catch (err) {
      console.error('Failed to load folders:', err);
    }
  }

  async function fetchTags() {
    try {
      const tags = await API.getTags();
      state.tags = tags;
      renderTagCloud();
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  }

  async function fetchAndRenderFiles() {
    try {
      let queryFolderId = null;
      let queryTag = null;
      let querySearch = state.searchMode === 'filter' ? state.searchQuery : null;

      if (state.currentFilter.type === 'folder') {
        queryFolderId = state.currentFilter.value;
      } else if (state.currentFilter.type === 'uncategorized') {
        queryFolderId = 0;
      } else if (state.currentFilter.type === 'tag') {
        queryTag = state.currentFilter.value;
      }

      const files = await API.getFiles({
        folderId: queryFolderId,
        tag: queryTag,
        search: querySearch,
        sortBy: state.sortBy
      });

      state.files = files;
      renderFileGrid(files);
      updateCatalogCounts();
    } catch (err) {
      showToast('Failed to fetch files: ' + err.message, 'error');
    }
  }

  // ============================================================================
  // RENDERING FUNCTIONS
  // ============================================================================

  function renderFolders() {
    elements.folderList.innerHTML = '';
    state.folders.forEach(f => {
      const li = document.createElement('li');
      li.className = 'folder-item';
      if (state.currentFilter.type === 'folder' && state.currentFilter.value === f.id) {
        li.classList.add('active');
      }

      li.innerHTML = `
        <span class="folder-color-tag" style="background-color: ${f.color || '#C09543'}"></span>
        <span class="folder-label" title="${f.description || f.name}">${escapeHtml(f.name)}</span>
        <span class="count-badge">${f.file_count || 0}</span>
        <button class="folder-delete-action" title="Delete folder">
          <i class="fa-solid fa-xmark"></i>
        </button>
      `;

      li.addEventListener('click', (e) => {
        if (e.target.closest('.folder-delete-action')) {
          e.stopPropagation();
          handleDeleteFolder(f.id, f.name);
          return;
        }
        setFolderFilter(f.id, f.name);
        if (window.innerWidth <= 960) elements.sidebar.classList.remove('open');
      });

      elements.folderList.appendChild(li);
    });
  }

  function renderTagCloud() {
    elements.tagCloud.innerHTML = '';
    if (!state.tags || state.tags.length === 0) {
      elements.tagCloud.innerHTML = '<div class="empty-subtext">No tags cataloged yet.</div>';
      return;
    }

    state.tags.forEach(t => {
      const pill = document.createElement('button');
      pill.className = 'tag-pill';
      if (state.currentFilter.type === 'tag' && state.currentFilter.value.toLowerCase() === t.name.toLowerCase()) {
        pill.classList.add('active');
      }

      pill.innerHTML = `
        <span>#${escapeHtml(t.name)}</span>
        <span class="tag-count">(${t.count})</span>
      `;

      pill.addEventListener('click', () => {
        if (state.currentFilter.type === 'tag' && state.currentFilter.value.toLowerCase() === t.name.toLowerCase()) {
          setNavFilter('all');
        } else {
          setTagFilter(t.name);
        }
        if (window.innerWidth <= 960) elements.sidebar.classList.remove('open');
      });

      elements.tagCloud.appendChild(pill);
    });
  }

  function renderFileGrid(files) {
    elements.fileGrid.innerHTML = '';
    elements.resultCountPill.textContent = `${files.length} item${files.length === 1 ? '' : 's'}`;

    if (!files || files.length === 0) {
      elements.emptyState.classList.remove('hidden');
      if (state.currentFilter.type === 'tag') {
        elements.emptyTitle.textContent = `No documents tagged #${state.currentFilter.value}`;
        elements.emptyDescription.textContent = 'Upload or tag files with this subject label.';
      } else if (state.currentFilter.type === 'folder') {
        elements.emptyTitle.textContent = 'This collection is empty';
        elements.emptyDescription.textContent = 'Move existing documents here or ingest new files.';
      } else if (state.isSearching) {
        elements.emptyTitle.textContent = 'No matching archival records found';
        elements.emptyDescription.textContent = 'Try adjusting query keywords or search phrasing.';
      } else {
        elements.emptyTitle.textContent = 'Archive Chamber is Empty';
        elements.emptyDescription.textContent = 'Drop files above or click Catalog File to commence auto-tagging and indexing.';
      }
      return;
    }

    elements.emptyState.classList.add('hidden');

    files.forEach(f => {
      const card = document.createElement('div');
      card.className = 'catalog-card';
      const ext = (f.extension || '').replace('.', '').toUpperCase() || 'FILE';
      const deweyCode = formatDeweyId(f.id);

      // Render up to 4 tags
      const tagHtml = (f.tags || []).slice(0, 4).map(t => {
        const tagName = typeof t === 'string' ? t : t.name;
        return `<span class="card-tag-pill">#${escapeHtml(tagName)}</span>`;
      }).join('');

      card.innerHTML = `
        <div class="card-top">
          <span class="card-type-badge"><i class="${getFileIconClass(f.extension)}"></i> ${ext}</span>
          <span class="card-dewey-badge">CAT-${deweyCode}</span>
        </div>

        <h3 class="card-title" title="${escapeHtml(f.original_name)}">${escapeHtml(f.original_name)}</h3>

        <div class="card-summary" title="${escapeHtml(f.summary || 'No summary available.')}">
          ${escapeHtml(f.summary || 'Summary pending processing...')}
        </div>

        <div class="card-tags">
          ${tagHtml}
        </div>

        <div class="card-footer">
          <div class="card-folder-badge">
            <i class="fa-regular fa-folder" style="color:${f.folder_color || 'inherit'}"></i>
            <span>${escapeHtml(f.folder_name || 'Unassigned')}</span>
          </div>

          <div class="card-actions">
            <a href="/api/files/${f.id}/download" download class="card-action-btn" title="Download Document" onclick="event.stopPropagation()">
              <i class="fa-solid fa-download"></i>
            </a>
            <button class="card-action-btn delete-btn" title="Delete Document" onclick="event.stopPropagation()">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </div>
        </div>
      `;

      // Open inspector drawer on click
      card.addEventListener('click', () => {
        openInspector(f.id);
      });

      // Delete button listener
      const deleteBtn = card.querySelector('.delete-btn');
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleDeleteFile(f.id, f.original_name);
      });

      elements.fileGrid.appendChild(card);
    });
  }

  function populateFolderDropdowns() {
    elements.drawerFolderSelect.innerHTML = '<option value="0">Uncategorized</option>';
    state.folders.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f.id;
      opt.textContent = f.name;
      elements.drawerFolderSelect.appendChild(opt);
    });
  }

  function updateCatalogCounts() {
    API.getFiles().then(allFiles => {
      elements.totalFilesBadge.textContent = allFiles.length;
      const uncategorizedCount = allFiles.filter(f => !f.folder_id).length;
      elements.uncategorizedBadge.textContent = uncategorizedCount;
    }).catch(() => {});
  }

  // ============================================================================
  // FILTERING & NAVIGATION
  // ============================================================================

  function setNavFilter(type) {
    state.currentFilter = { type: type, value: null };
    state.isSearching = false;
    elements.searchBanner.classList.add('hidden');
    elements.clearTagFilterBtn.classList.add('hidden');

    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.filter === type);
    });
    document.querySelectorAll('.folder-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tag-pill').forEach(el => el.classList.remove('active'));

    elements.currentViewName.textContent = type === 'uncategorized' ? 'Uncategorized Documents' : 'All Documents';
    fetchAndRenderFiles();
  }

  function setFolderFilter(folderId, folderName) {
    state.currentFilter = { type: 'folder', value: folderId };
    state.isSearching = false;
    elements.searchBanner.classList.add('hidden');
    elements.clearTagFilterBtn.classList.add('hidden');

    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    renderFolders();
    document.querySelectorAll('.tag-pill').forEach(el => el.classList.remove('active'));

    elements.currentViewName.textContent = folderName;
    fetchAndRenderFiles();
  }

  function setTagFilter(tagName) {
    state.currentFilter = { type: 'tag', value: tagName };
    state.isSearching = false;
    elements.searchBanner.classList.add('hidden');
    elements.clearTagFilterBtn.classList.remove('hidden');

    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.folder-item').forEach(el => el.classList.remove('active'));
    renderTagCloud();

    elements.currentViewName.textContent = `Subject: #${tagName}`;
    fetchAndRenderFiles();
  }

  // ============================================================================
  // SEARCH FUNCTIONALITY ("ASK AI" vs KEYWORD)
  // ============================================================================

  function setSearchMode(mode) {
    state.searchMode = mode;
    elements.searchModeAsk.classList.toggle('active', mode === 'ask');
    elements.searchModeFilter.classList.toggle('active', mode === 'filter');

    if (mode === 'ask') {
      elements.searchInput.placeholder = "Ask AI in natural language e.g. 'budget spreadsheets from last month'...";
    } else {
      elements.searchInput.placeholder = "Instant keyword filter (names, summaries, tags)...";
    }
  }

  async function performSearch() {
    const query = elements.searchInput.value.trim();
    if (!query) return;

    if (state.searchMode === 'filter') {
      state.searchQuery = query;
      fetchAndRenderFiles();
      return;
    }

    // Natural Language Search ("Ask" mode)
    try {
      showToast('Consulting AI catalog retrieval engine...', 'info');
      elements.searchSubmitBtn.disabled = true;
      elements.searchSubmitBtn.textContent = 'Inquiring...';

      const result = await API.askSearch(query);

      state.isSearching = true;
      elements.searchBanner.classList.remove('hidden');
      elements.bannerHeading.textContent = `AI Search: "${query}"`;
      elements.bannerExplanation.textContent = result.explanation || 'Analyzed document semantics and ranked matches.';

      elements.currentViewName.textContent = `Ask AI: "${query}"`;
      renderFileGrid(result.files);

    } catch (err) {
      showToast('Search query failed: ' + err.message, 'error');
    } finally {
      elements.searchSubmitBtn.disabled = false;
      elements.searchSubmitBtn.textContent = 'Search';
    }
  }

  function resetSearch() {
    elements.searchInput.value = '';
    elements.searchClearBtn.classList.add('hidden');
    elements.searchBanner.classList.add('hidden');
    state.searchQuery = '';
    state.isSearching = false;
    setNavFilter('all');
  }

  // ============================================================================
  // FILE INGESTION (UPLOAD & AUTO-TAGGING)
  // ============================================================================

  async function handleFileUpload(files) {
    if (!files || files.length === 0) return;

    try {
      elements.uploadProgress.classList.remove('hidden');
      showToast(`Ingesting ${files.length} document${files.length > 1 ? 's' : ''}... extracting text & auto-tagging.`, 'info');

      // Associate with current folder if viewing a folder
      const targetFolderId = state.currentFilter.type === 'folder' ? state.currentFilter.value : null;

      const response = await API.uploadFiles(files, targetFolderId);
      showToast(`Successfully cataloged ${response.count} document${response.count > 1 ? 's' : ''}!`, 'success');

      elements.fileInput.value = '';
      await fetchFolders();
      await fetchTags();
      await fetchSystemStatus();
      await fetchAndRenderFiles();

    } catch (err) {
      showToast('Upload failed: ' + err.message, 'error');
    } finally {
      elements.uploadProgress.classList.add('hidden');
    }
  }

  async function handleDeleteFile(fileId, fileName = 'this file') {
    if (!confirm(`Are you sure you wish to expunge "${fileName}" from the archive?`)) return;

    try {
      await API.deleteFile(fileId);
      showToast('Document expunged from archive.', 'success');
      if (state.activeFileId === fileId) {
        closeInspector();
      }
      await fetchFolders();
      await fetchTags();
      await fetchSystemStatus();
      await fetchAndRenderFiles();
    } catch (err) {
      showToast('Failed to delete file: ' + err.message, 'error');
    }
  }

  // ============================================================================
  // INSPECTOR & CHAT DRAWER
  // ============================================================================

  async function openInspector(fileId) {
    state.activeFileId = fileId;
    elements.inspectorBackdrop.classList.remove('hidden');
    elements.inspectorDrawer.classList.add('open');

    try {
      const file = await API.getFileDetails(fileId);
      state.activeFile = file;
      renderInspectorDossier(file);
      switchDrawerTab(state.activeTab);

      if (state.activeTab === 'chat') {
        loadChatHistory(fileId);
      }
    } catch (err) {
      showToast('Failed to load file dossier: ' + err.message, 'error');
      closeInspector();
    }
  }

  function closeInspector() {
    elements.inspectorDrawer.classList.remove('open');
    elements.inspectorBackdrop.classList.add('hidden');
    state.activeFileId = null;
    state.activeFile = null;
  }

  function switchDrawerTab(tabName) {
    state.activeTab = tabName;
    elements.tabDossierBtn.classList.toggle('active', tabName === 'dossier');
    elements.tabChatBtn.classList.toggle('active', tabName === 'chat');
    elements.tabDossier.classList.toggle('active', tabName === 'dossier');
    elements.tabChat.classList.toggle('active', tabName === 'chat');

    if (tabName === 'chat' && state.activeFileId) {
      loadChatHistory(state.activeFileId);
    }
  }

  function renderInspectorDossier(file) {
    const ext = (file.extension || '').replace('.', '').toUpperCase() || 'FILE';
    elements.drawerFileExt.textContent = ext;
    elements.drawerFileName.textContent = file.original_name;
    elements.drawerDownloadBtn.href = `/api/files/${file.id}/download`;

    // Summary
    elements.drawerSummary.textContent = file.summary || 'No AI summary generated for this document yet.';

    // Tags
    renderDrawerTags(file.tags || []);

    // Folder select
    elements.drawerFolderSelect.value = file.folder_id || '0';

    // Physical attributes
    elements.drawerFileSize.textContent = formatBytes(file.file_size);
    elements.drawerMime.textContent = file.mime_type || 'Unknown';
    elements.drawerDate.textContent = formatDate(file.uploaded_at);
    elements.drawerPath.textContent = file.file_path ? file.file_path.split('\\').pop().split('/').pop() : 'Internal';

    // Extracted text preview
    elements.drawerTextPreview.textContent = file.extracted_text || '[No readable text content extracted from this document format.]';
  }

  function renderDrawerTags(tags) {
    elements.drawerTagList.innerHTML = '';
    if (!tags || tags.length === 0) {
      elements.drawerTagList.innerHTML = '<span class="empty-subtext">No tags attached.</span>';
      return;
    }

    tags.forEach(t => {
      const chip = document.createElement('span');
      chip.className = 'drawer-tag-chip';
      chip.innerHTML = `
        <span>#${escapeHtml(t.name)}</span>
        <button class="remove-tag-btn" title="Remove tag">&times;</button>
      `;

      chip.querySelector('.remove-tag-btn').addEventListener('click', async () => {
        try {
          const res = await API.removeTag(state.activeFileId, t.id);
          state.activeFile.tags = res.tags;
          renderDrawerTags(res.tags);
          fetchTags();
          fetchAndRenderFiles();
        } catch (err) {
          showToast('Failed to remove tag: ' + err.message, 'error');
        }
      });

      elements.drawerTagList.appendChild(chip);
    });
  }

  async function handleAddTag(e) {
    e.preventDefault();
    const tagName = elements.newTagInput.value.trim();
    if (!tagName || !state.activeFileId) return;

    try {
      const res = await API.addTag(state.activeFileId, tagName);
      elements.newTagInput.value = '';
      state.activeFile.tags = res.tags;
      renderDrawerTags(res.tags);
      showToast(`Tag #${tagName} added.`, 'success');
      await fetchTags();
      await fetchAndRenderFiles();
    } catch (err) {
      showToast('Failed to add tag: ' + err.message, 'error');
    }
  }

  async function handleFolderAssignment(e) {
    const folderId = parseInt(e.target.value, 10);
    if (!state.activeFileId) return;

    try {
      await API.updateFolderAssignment(state.activeFileId, folderId > 0 ? folderId : null);
      showToast('Document moved to collection.', 'success');
      await fetchFolders();
      await fetchAndRenderFiles();
    } catch (err) {
      showToast('Failed to move document: ' + err.message, 'error');
    }
  }

  async function handleReprocessAi() {
    if (!state.activeFileId) return;
    try {
      elements.reprocessAiBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
      const updatedFile = await API.reprocessAi(state.activeFileId);
      state.activeFile = updatedFile;
      renderInspectorDossier(updatedFile);
      showToast('AI analysis updated successfully.', 'success');
      await fetchTags();
      await fetchAndRenderFiles();
    } catch (err) {
      showToast('Reprocess failed: ' + err.message, 'error');
    } finally {
      elements.reprocessAiBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Re-analyze';
    }
  }

  function copyExtractedText() {
    const text = elements.drawerTextPreview.textContent;
    navigator.clipboard.writeText(text).then(() => {
      showToast('Extracted text copied to clipboard.', 'success');
    }).catch(() => {
      showToast('Could not copy to clipboard.', 'error');
    });
  }

  // ============================================================================
  // DOCUMENT CHAT
  // ============================================================================

  async function loadChatHistory(fileId) {
    try {
      const data = await API.getChatHistory(fileId);
      renderChatMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }

  function renderChatMessages(messages) {
    elements.chatMessageLog.innerHTML = '';

    if (!messages || messages.length === 0) {
      elements.chatMessageLog.innerHTML = `
        <div class="empty-subtext" style="text-align:center; padding: 2rem 0;">
          No inquiries made yet. Select a starter question above or type your prompt below.
        </div>
      `;
      return;
    }

    messages.forEach(msg => {
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${msg.role}`;
      bubble.innerHTML = formatMarkdown(msg.content);
      elements.chatMessageLog.appendChild(bubble);
    });

    elements.chatMessageLog.scrollTop = elements.chatMessageLog.scrollHeight;
  }

  async function handleChatSubmit(e) {
    e.preventDefault();
    const prompt = elements.chatInputText.value.trim();
    if (!prompt || !state.activeFileId) return;

    // Append user message immediately
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = prompt;
    elements.chatMessageLog.appendChild(userBubble);

    // Append typing indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble assistant';
    typingBubble.innerHTML = '<i class="fa-solid fa-feather-pointed fa-bounce"></i> Reading document and composing response...';
    elements.chatMessageLog.appendChild(typingBubble);
    elements.chatMessageLog.scrollTop = elements.chatMessageLog.scrollHeight;

    elements.chatInputText.value = '';

    try {
      const res = await API.sendChatMessage(state.activeFileId, prompt);
      typingBubble.innerHTML = formatMarkdown(res.message.content);
      elements.chatMessageLog.scrollTop = elements.chatMessageLog.scrollHeight;
    } catch (err) {
      typingBubble.innerHTML = `<span style="color:var(--seal-crimson)"><i class="fa-solid fa-triangle-exclamation"></i> Error: ${escapeHtml(err.message)}</span>`;
    }
  }

  async function handleClearChatHistory() {
    if (!state.activeFileId) return;
    if (!confirm('Clear all conversation turns for this document?')) return;

    try {
      await API.clearChatHistory(state.activeFileId);
      elements.chatMessageLog.innerHTML = `
        <div class="empty-subtext" style="text-align:center; padding: 2rem 0;">
          Conversation cleared.
        </div>
      `;
      showToast('Chat history cleared.', 'info');
    } catch (err) {
      showToast('Failed to clear chat: ' + err.message, 'error');
    }
  }

  // ============================================================================
  // FOLDER CREATION MODAL
  // ============================================================================

  function openFolderModal() {
    elements.newFolderModal.classList.remove('hidden');
    elements.folderNameInput.value = '';
    elements.folderDescInput.value = '';
    elements.folderNameInput.focus();
  }

  function closeFolderModal() {
    elements.newFolderModal.classList.add('hidden');
  }

  async function handleCreateFolder(e) {
    e.preventDefault();
    const name = elements.folderNameInput.value.trim();
    const desc = elements.folderDescInput.value.trim();
    const colorInput = document.querySelector('input[name="folderColor"]:checked');
    const color = colorInput ? colorInput.value : '#C09543';

    if (!name) return;

    try {
      const folder = await API.createFolder(name, desc, color);
      showToast(`Collection "${folder.name}" established.`, 'success');
      closeFolderModal();
      await fetchFolders();
      setFolderFilter(folder.id, folder.name);
    } catch (err) {
      showToast('Failed to create folder: ' + err.message, 'error');
    }
  }

  async function handleDeleteFolder(folderId, folderName) {
    if (!confirm(`Dissolve collection "${folderName}"? Contained documents will become Uncategorized.`)) return;

    try {
      await API.deleteFolder(folderId);
      showToast(`Collection "${folderName}" removed.`, 'info');
      if (state.currentFilter.type === 'folder' && state.currentFilter.value === folderId) {
        setNavFilter('all');
      } else {
        await fetchFolders();
        await fetchAndRenderFiles();
      }
    } catch (err) {
      showToast('Failed to delete folder: ' + err.message, 'error');
    }
  }

  // ============================================================================
  // TOAST NOTIFICATIONS & UTILITIES
  // ============================================================================

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
      <i class="fa-solid ${icon}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatDate(isoStr) {
    if (!isoStr) return 'Recent';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (_) {
      return isoStr;
    }
  }

  function formatDeweyId(id) {
    return String(id).padStart(4, '0');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let parsed = escapeHtml(text);
    // Bold
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    parsed = parsed.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Blockquote
    parsed = parsed.replace(/^&gt;\s?(.*)$/gm, '<blockquote>$1</blockquote>');
    // Code ticks
    parsed = parsed.replace(/`([^`]+)`/g, '<code style="background:var(--bg-parchment-deep);padding:1px 4px;border-radius:3px;">$1</code>');
    // Newlines
    parsed = parsed.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
    return parsed;
  }

  function getFileIconClass(extension) {
    const ext = (extension || '').toLowerCase();
    if (ext === '.pdf') return 'fa-regular fa-file-pdf';
    if (ext === '.csv' || ext === '.tsv') return 'fa-solid fa-file-csv';
    if (ext === '.json' || ext === '.xml' || ext === '.yaml' || ext === '.yml') return 'fa-regular fa-file-code';
    if (['.py', '.js', '.ts', '.html', '.css', '.java', '.sql'].includes(ext)) return 'fa-solid fa-code';
    if (ext === '.md' || ext === '.markdown') return 'fa-regular fa-file-lines';
    if (ext === '.docx' || ext === '.doc') return 'fa-regular fa-file-word';
    return 'fa-regular fa-file';
  }
});
