import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import toast, { Toaster } from 'react-hot-toast';
import ModelViewer from './components/ModelViewer';

const API_URL = "http://localhost:8000";

function getContrastTextColor(hexColor) {
  if (!hexColor) return "#FFFFFF";
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return (yiq >= 128) ? '#000000' : '#FFFFFF';
}

function Expander({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-700/50 rounded-lg mb-3 bg-[#1e2128] overflow-hidden shadow-sm">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full p-2.5 text-left font-bold text-xs text-gray-300 flex justify-between hover:bg-gray-700/80 transition">
        {title} <span className="text-gray-500">{isOpen ? '▲' : '▼'}</span>
      </button>
      {isOpen && <div className="p-4 border-t border-gray-700/50 bg-[#16181d]">{children}</div>}
    </div>
  );
}

function TransformSlider({ label, min, max, step, value, onChange }) {
  return (
    <div className="flex flex-col mb-3">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">{label}</span>
        <input 
          type="number" value={value} 
          onChange={e => onChange(parseFloat(e.target.value))} 
          className="w-14 bg-[#0e1117] text-white text-[11px] border border-gray-600 rounded px-1 py-0.5 text-center outline-none focus:border-blue-500" 
        />
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(parseFloat(e.target.value))} className="w-full accent-blue-500 cursor-pointer" />
    </div>
  );
}

function DraggableMaterialBadge({ materialName, colorHex }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: `mat-${materialName}`, data: { type: 'material', name: materialName } });
  const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 50, position: 'relative' } : undefined;
  return (
    <div ref={setNodeRef} {...listeners} {...attributes} className="cursor-grab px-3 py-1.5 m-1 rounded-md shadow-md text-[11px] font-semibold text-center border border-gray-500/30 hover:scale-105 transition-transform" style={{ ...style, backgroundColor: colorHex, color: getContrastTextColor(colorHex) }}>
      {materialName}
    </div>
  );
}

function DraggableScenarioBadge({ scenarioName }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: `scn-${scenarioName}`, data: { type: 'scenario', name: scenarioName } });
  const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 50, position: 'relative' } : undefined;
  const imgUrl = `https://via.placeholder.com/150x80/2a2e38/ffffff?text=${scenarioName.replace('.blend','')}`;
  return (
    <div ref={setNodeRef} {...listeners} {...attributes} className="cursor-grab relative m-1 rounded-md overflow-hidden border border-gray-600 hover:border-blue-400 hover:scale-105 transition-all w-24 h-16 flex flex-col group shadow-md" style={style}>
      <img src={imgUrl} alt="cenario" className="w-full h-10 object-cover" />
      <div className="bg-gray-800 text-white text-[9px] text-center py-1 flex-1 font-bold truncate px-1 shadow-inner">{scenarioName.replace('.blend', '')}</div>
    </div>
  );
}

function DroppableModelCard({ model, onSelect, isActive, catalog, onRemoveModel, onRemoveItem }) {
  const { isOver, setNodeRef } = useDroppable({ id: model.name });
  return (
    <div ref={setNodeRef} onClick={() => onSelect(model.name)} className={`p-3 rounded-lg mb-3 cursor-pointer border-2 transition-all ${isActive ? 'border-blue-500 bg-[#2b303b]' : 'border-gray-700 bg-[#1e2128] hover:bg-[#262a33]'} ${isOver ? 'ring-2 ring-green-400 border-transparent shadow-[0_0_15px_rgba(74,222,128,0.3)]' : ''}`}>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-xs font-bold truncate w-3/4" title={model.name}>{model.name}</h3>
        <button onClick={(e) => { e.stopPropagation(); onRemoveModel(model.name); }} className="text-gray-500 hover:text-red-400 text-xs">🗑️</button>
      </div>
      <div className="pointer-events-none rounded overflow-hidden border border-gray-800">
         <ModelViewer fileUrl={model.localUrl} color={model.materiais.length > 0 && catalog[model.materiais[0]] ? catalog[model.materiais[0]].cor_hex : "#808080"} />
      </div>
      <div className="mt-3">
        <span className="text-[9px] uppercase tracking-wider text-gray-500 font-bold block mb-1">Cores:</span>
        <div className="flex flex-wrap gap-1">
          {model.materiais.map(mat => {
            const hex = catalog[mat] ? catalog[mat].cor_hex : '#555';
            return (
              <span key={mat} className="group relative px-2 py-0.5 text-[10px] font-semibold rounded shadow-sm border border-black/20 flex items-center gap-1.5" style={{backgroundColor: hex, color: getContrastTextColor(hex)}}>
                {mat}
                <button onClick={(e) => { e.stopPropagation(); onRemoveItem(model.name, 'material', mat); }} className="opacity-40 hover:opacity-100 font-bold px-0.5">×</button>
              </span>
            )
          })}
        </div>
      </div>
      <div className="mt-2">
        <span className="text-[9px] uppercase tracking-wider text-gray-500 font-bold block mb-1">Cenários:</span>
        <div className="flex flex-wrap gap-1">
          {model.cenarios.map(scn => (
            <span key={scn} className="group px-2 py-0.5 text-[10px] font-semibold rounded shadow-sm border border-gray-600 bg-gray-700 text-white flex items-center gap-1.5">
              {scn.replace('.blend','')}
              <button onClick={(e) => { e.stopPropagation(); onRemoveItem(model.name, 'scenario', scn); }} className="opacity-40 hover:opacity-100 text-red-300 font-bold px-0.5">×</button>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [models, setModels] = useState({});
  const [activeModel, setActiveModel] = useState(null);
  const [catalog, setCatalog] = useState({});
  const [availableScenarios, setAvailableScenarios] = useState(["template_ecommerce.blend"]);
  const [globalConfig, setGlobalConfig] = useState({ prev_res: 30, prev_samples: 16, res_producao: 100, samples: 64, max_time: 0, auto_orient: false, multiplicador_luz_cena: 1.0 });
  const [matEditName, setMatEditName] = useState("");
  const [matEditProps, setMatEditProps] = useState({ cor_hex: "#808080", roughness: 0.6, metallic: 0.0, specular: 0.5, transmission: 0.0, subsurface: 0.0 });
  
  const [logs, setLogs] = useState("Aguardando execução...\n");
  const [generatedImages, setGeneratedImages] = useState([]);
  const [isRendering, setIsRendering] = useState(false);
  const [showPreviewConfig, setShowPreviewConfig] = useState(false);
  const logEndRef = useRef(null);

  // --- ESTADO DO MODAL CUSTOMIZADO (Fim do Alert nativo) ---
  const [promptModal, setPromptModal] = useState({ isOpen: false, value: '' });

  useEffect(() => {
    axios.get(`${API_URL}/config`).then(res => {
      setCatalog(res.data.materiais || {});
      if (res.data.cenarios_disponiveis && res.data.cenarios_disponiveis.length > 0) setAvailableScenarios(res.data.cenarios_disponiveis);
      if (res.data.config_app) setGlobalConfig(res.data.config_app);
      const firstMat = Object.keys(res.data.materiais || {})[0];
      if (firstMat) loadMaterialIntoEditor(firstMat, res.data.materiais);
    });
  }, []);

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [logs]);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    for (let file of files) {
      if(!models[file.name]) {
        const localUrl = URL.createObjectURL(file);
        setModels(prev => ({
          ...prev, [file.name]: {
            name: file.name, localUrl: localUrl, materiais: ["PLA - Preto"], cenarios: [availableScenarios[0]],
            r_tx: 0, r_ty: 0, r_tz: 0, r_rx: 0, r_ry: 0, r_rz: 0, r_sx: 1, r_sy: 1, r_sz: 1, r_scale_locked: true,
            s_tx: 0, s_ty: 0, s_tz: 0, s_rx: 0, s_ry: 0, s_rz: 0, s_sx: 1, s_sy: 1, s_sz: 1, s_scale_locked: true,
            perfil: "020_standard"
          }
        }));
        if (!activeModel) setActiveModel(file.name);
        const formData = new FormData(); formData.append("file", file);
        await axios.post(`${API_URL}/upload`, formData);
      }
    }
  };

  const removeModel = (name) => {
    setModels(prev => { const newModels = {...prev}; delete newModels[name]; return newModels; });
    if(activeModel === name) setActiveModel(null);
  };

  const removeItemFromModel = (modelName, type, itemName) => {
    setModels(prev => {
      const mod = prev[modelName];
      if (type === 'material') {
         const newMats = mod.materiais.filter(m => m !== itemName);
         return { ...prev, [modelName]: { ...mod, materiais: newMats.length ? newMats : ["PLA - Preto"] } };
      }
      if (type === 'scenario') {
         const newScns = mod.cenarios.filter(s => s !== itemName);
         return { ...prev, [modelName]: { ...mod, cenarios: newScns.length ? newScns : [availableScenarios[0]] } };
      }
      return prev;
    });
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (over && active.data.current) {
      const { type, name } = active.data.current;
      const targetModel = over.id;
      setModels(prev => {
        const mod = prev[targetModel];
        if (type === 'material' && !mod.materiais.includes(name)) {
           toast.success(`Cor ${name} adicionada!`, {style: {background: '#333', color: '#fff'}});
           return { ...prev, [targetModel]: { ...mod, materiais: [...mod.materiais, name] } };
        }
        if (type === 'scenario' && !mod.cenarios.includes(name)) {
           toast.success(`Cenário adicionado!`, {style: {background: '#333', color: '#fff'}});
           return { ...prev, [targetModel]: { ...mod, cenarios: [...mod.cenarios, name] } };
        }
        return prev;
      });
    }
  };

  const updateModel = (key, value) => {
    if(!activeModel) return;
    setModels(prev => ({ ...prev, [activeModel]: { ...prev[activeModel], [key]: value } }));
  };

  const loadMaterialIntoEditor = (name, currentCatalog = catalog) => {
    setMatEditName(name); if(currentCatalog[name]) setMatEditProps(currentCatalog[name]);
  };

  const saveConfigToBackend = async (newCatalog) => {
    await axios.post(`${API_URL}/save_config`, { config_app: globalConfig, materiais: newCatalog });
  };

  const handleMatPropChange = (prop, val) => {
    const newProps = { ...matEditProps, [prop]: val };
    setMatEditProps(newProps);
    const newCatalog = { ...catalog, [matEditName]: newProps };
    setCatalog(newCatalog); saveConfigToBackend(newCatalog);
  };

  // Aciona o Modal em vez do prompt nativo
  const openSaveMaterialModal = () => {
    setPromptModal({ isOpen: true, value: `${matEditName} Novo` });
  };

  // Confirma a criação do material a partir do Modal
  const confirmSaveNewMaterial = () => {
    const newName = promptModal.value.trim();
    if (newName && !catalog[newName]) {
      const newCatalog = { ...catalog, [newName]: matEditProps };
      setCatalog(newCatalog); setMatEditName(newName); saveConfigToBackend(newCatalog);
      toast.success(`Material criado!`, {icon: '🎨'});
      setPromptModal({ isOpen: false, value: '' });
    } else {
      toast.error('Nome inválido ou já existe no catálogo.');
    }
  };

  // --- NOVA LÓGICA DE DOWNLOAD EM ZIP ---
  const downloadAllImagesAsZip = async () => {
    if (generatedImages.length === 0) return;
    const tId = toast.loading("Compactando imagens...", {icon: '📦'});
    try {
      const paths = generatedImages.map(img => img.rawPath); // Usa o path real do sistema
      const response = await axios.post(`${API_URL}/download-zip`, { paths }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Renders_3PTR_${new Date().getTime()}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Download concluído!", {id: tId});
    } catch (err) {
      toast.error("Erro ao gerar ZIP.", {id: tId});
    }
  };

  const downloadLog = () => {
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `log_3ptr_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
    a.click(); URL.revokeObjectURL(url);
    toast.success("Log baixado!");
  };

  const startRender = async (isPreview) => {
    if (Object.keys(models).length === 0) return toast.error("Importe um modelo primeiro!");
    setLogs(prev => prev + `\n\n=== INICIANDO ${isPreview ? 'PREVIEW' : 'PRODUÇÃO'} (${new Date().toLocaleTimeString()}) ===\n`);
    setGeneratedImages([]); setIsRendering(true); setShowPreviewConfig(false); 
    toast.loading(isPreview ? "Renderizando Preview..." : "Renderizando Lote...", {id: 'render'});

    const taskList = isPreview && activeModel ? [models[activeModel]] : Object.values(models);
    const mappedTasks = taskList.map(mod => ({
      modelo_nome: mod.name, materiais: mod.materiais, cenarios: mod.cenarios,
      s_tx: mod.s_tx || 0, s_ty: mod.s_ty || 0, s_tz: mod.s_tz || 0,
      s_rx: mod.s_rx || 0, s_ry: mod.s_ry || 0, s_rz: mod.s_rz || 0,
      s_sx: mod.s_sx || 1, s_sy: mod.s_sy || 1, s_sz: mod.s_sz || 1,
      r_tx: mod.r_tx || 0, r_ty: mod.r_ty || 0, r_tz: mod.r_tz || 0,
      r_rx: mod.r_rx || 0, r_ry: mod.r_ry || 0, r_rz: mod.r_rz || 0,
      r_sx: mod.r_sx || 1, r_sy: mod.r_sy || 1, r_sz: mod.r_sz || 1,
      perfil: mod.perfil
    }));

    const payload = {
      tasks: mappedTasks, is_preview: isPreview,
      samples: isPreview ? globalConfig.prev_samples : globalConfig.samples,
      resolucao: isPreview ? globalConfig.prev_res : globalConfig.res_producao,
      auto_orient: globalConfig.auto_orient
    };

    try {
      const response = await fetch(`${API_URL}/render`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!response.ok) { toast.error(`Erro na API: ${response.status}`, {id: 'render'}); setIsRendering(false); return; }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');
        
        for (let line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            if (data.type === 'log') setLogs(prev => prev + data.text);
            else if (data.type === 'image') {
              const cacheBuster = Date.now();
              // Salvamos a URL de exibição e o rawPath (caminho real) para o ZIP
              setGeneratedImages(prev => [...prev, {
                cam: data.camera, mat: data.material, scn: data.cenario.replace('.blend',''), 
                url: `${API_URL}/image?path=${encodeURIComponent(data.path)}&t=${cacheBuster}`,
                rawPath: data.path 
              }]);
            } else if (data.type === 'done') {
              toast.success("Finalizado!", {id: 'render'}); setIsRendering(false);
            }
          }
        }
      }
    } catch (err) { toast.error("Erro na conexão com API", {id: 'render'}); setIsRendering(false); }
  };

  const m = activeModel ? models[activeModel] : null;

  return (
    <div className="flex h-screen bg-[#0e1117] text-white font-sans overflow-hidden">
      <Toaster position="bottom-right" toastOptions={{ style: { background: '#333', color: '#fff', fontSize: '14px' } }} />

      {/* --- MODAL CUSTOMIZADO (SOFT NOTIFICATION) --- */}
      {promptModal.isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center transition-opacity">
          <div className="bg-[#1e2128] border border-gray-700 p-6 rounded-xl shadow-2xl w-96 transform scale-100">
            <h3 className="text-white font-bold mb-2">Salvar Novo Material</h3>
            <p className="text-xs text-gray-400 mb-4">Escolha um nome único para este material no catálogo.</p>
            <input 
              type="text" value={promptModal.value}
              onChange={e => setPromptModal({...promptModal, value: e.target.value})}
              className="w-full bg-[#0e1117] border border-gray-600 rounded p-2.5 text-white outline-none focus:border-blue-500 transition mb-6 font-semibold"
              autoFocus
              onKeyDown={e => { if(e.key === 'Enter') confirmSaveNewMaterial(); }}
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => setPromptModal({isOpen: false, value: ''})} className="px-4 py-2 text-sm font-bold rounded text-gray-400 hover:text-white transition">Cancelar</button>
              <button onClick={confirmSaveNewMaterial} className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded font-bold shadow-lg transition">Salvar</button>
            </div>
          </div>
        </div>
      )}

      <div className="w-80 bg-[#16181d] flex flex-col h-full border-r border-gray-800 shadow-2xl z-10">
        <div className="p-4 border-b border-gray-800">
          <label className="flex flex-col items-center justify-center w-full h-16 border border-dashed border-gray-600 rounded cursor-pointer bg-[#1e2128] hover:bg-gray-800 hover:border-blue-500 transition">
            <span className="text-xs text-gray-400 font-bold">+ IMPORTAR STL</span>
            <input type="file" multiple accept=".stl" onChange={handleFileUpload} className="hidden" />
          </label>
        </div>
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <DndContext onDragEnd={handleDragEnd}>
            {Object.values(models).map(mod => (
              <DroppableModelCard key={mod.name} model={mod} onSelect={setActiveModel} isActive={activeModel === mod.name} catalog={catalog} onRemoveModel={removeModel} onRemoveItem={removeItemFromModel} />
            ))}
            <div className="mt-6 pt-4 border-t border-gray-800">
              <h3 className="text-[10px] font-bold text-gray-500 mb-3 uppercase text-center">🎨 Cores</h3>
              <div className="flex flex-wrap justify-center">
                {Object.entries(catalog).map(([name, data]) => (
                  <DraggableMaterialBadge key={name} materialName={name} colorHex={data.cor_hex} />
                ))}
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-800 mb-8">
              <h3 className="text-[10px] font-bold text-gray-500 mb-3 uppercase text-center">🎬 Cenários</h3>
              <div className="flex flex-wrap justify-center gap-2">
                {availableScenarios.map(scn => (
                  <DraggableScenarioBadge key={scn} scenarioName={scn} />
                ))}
              </div>
            </div>
          </DndContext>
        </div>
      </div>

      <div className="w-[420px] flex flex-col h-full bg-[#111318] border-r border-gray-800 relative z-10">
        <div className="p-4 bg-[#16181d] border-b border-gray-800">
          <h2 className="font-bold text-sm text-blue-400 truncate">{activeModel ? `🛠️ ${activeModel}` : "Nenhum Modelo"}</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          {m ? (
            <>
              <Expander title="🎬 Cena Blender (Pose Rápida)" defaultOpen={true}>
                <div className="grid grid-cols-2 gap-6 mb-2">
                  <div>
                    <h4 className="text-[10px] text-blue-400 mb-2 font-bold uppercase">Mover</h4>
                    <TransformSlider label="X" min="-150" max="150" step="1" value={m.r_tx} onChange={v => updateModel('r_tx', v)} />
                    <TransformSlider label="Y" min="-150" max="150" step="1" value={m.r_ty} onChange={v => updateModel('r_ty', v)} />
                    <TransformSlider label="Z" min="-150" max="150" step="1" value={m.r_tz} onChange={v => updateModel('r_tz', v)} />
                  </div>
                  <div>
                    <h4 className="text-[10px] text-green-400 mb-2 font-bold uppercase">Girar</h4>
                    <TransformSlider label="X°" min="-180" max="180" step="5" value={m.r_rx} onChange={v => updateModel('r_rx', v)} />
                    <TransformSlider label="Y°" min="-180" max="180" step="5" value={m.r_ry} onChange={v => updateModel('r_ry', v)} />
                    <TransformSlider label="Z°" min="-180" max="180" step="5" value={m.r_rz} onChange={v => updateModel('r_rz', v)} />
                  </div>
                </div>
                <div className="bg-gray-800/50 p-2 rounded border border-gray-700/50 mt-2">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-[10px] text-purple-400 font-bold uppercase">Escala</h4>
                    <button onClick={() => updateModel('r_scale_locked', !m.r_scale_locked)} className="text-[10px] bg-gray-700 px-2 py-1 rounded hover:bg-gray-600 transition text-white">
                      {m.r_scale_locked ? '🔒 Uniforme' : '🔓 Eixos'}
                    </button>
                  </div>
                  {m.r_scale_locked ? (
                    <TransformSlider label="Geral" min="0.1" max="5.0" step="0.1" value={m.r_sx} onChange={v => {updateModel('r_sx', v); updateModel('r_sy', v); updateModel('r_sz', v);}} />
                  ) : (
                    <div className="grid grid-cols-3 gap-2">
                      <TransformSlider label="X" min="0.1" max="5.0" step="0.1" value={m.r_sx} onChange={v => updateModel('r_sx', v)} />
                      <TransformSlider label="Y" min="0.1" max="5.0" step="0.1" value={m.r_sy} onChange={v => updateModel('r_sy', v)} />
                      <TransformSlider label="Z" min="0.1" max="5.0" step="0.1" value={m.r_sz} onChange={v => updateModel('r_sz', v)} />
                    </div>
                  )}
                </div>
              </Expander>

              <Expander title="🔪 Fatiador Slicer (Refaz a Malha)">
                 <div className="grid grid-cols-2 gap-6 mb-2">
                  <div>
                    <TransformSlider label="Mover X" min="-150" max="150" step="1" value={m.s_tx} onChange={v => updateModel('s_tx', v)} />
                    <TransformSlider label="Mover Y" min="-150" max="150" step="1" value={m.s_ty} onChange={v => updateModel('s_ty', v)} />
                    <TransformSlider label="Mover Z" min="-150" max="150" step="1" value={m.s_tz} onChange={v => updateModel('s_tz', v)} />
                  </div>
                  <div>
                    <TransformSlider label="Girar X°" min="-180" max="180" step="5" value={m.s_rx} onChange={v => updateModel('s_rx', v)} />
                    <TransformSlider label="Girar Y°" min="-180" max="180" step="5" value={m.s_ry} onChange={v => updateModel('s_ry', v)} />
                    <TransformSlider label="Girar Z°" min="-180" max="180" step="5" value={m.s_rz} onChange={v => updateModel('s_rz', v)} />
                  </div>
                </div>
                <div className="bg-gray-800/50 p-2 rounded border border-gray-700/50 mt-2">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-[10px] text-purple-400 font-bold uppercase">Escala Slicer</h4>
                    <button onClick={() => updateModel('s_scale_locked', !m.s_scale_locked)} className="text-[10px] bg-gray-700 px-2 py-1 rounded hover:bg-gray-600 transition text-white">
                      {m.s_scale_locked ? '🔒 Uniforme' : '🔓 Eixos'}
                    </button>
                  </div>
                  {m.s_scale_locked ? (
                    <TransformSlider label="Geral" min="0.1" max="5.0" step="0.1" value={m.s_sx} onChange={v => {updateModel('s_sx', v); updateModel('s_sy', v); updateModel('s_sz', v);}} />
                  ) : (
                    <div className="grid grid-cols-3 gap-2">
                      <TransformSlider label="X" min="0.1" max="5.0" step="0.1" value={m.s_sx} onChange={v => updateModel('s_sx', v)} />
                      <TransformSlider label="Y" min="0.1" max="5.0" step="0.1" value={m.s_sy} onChange={v => updateModel('s_sy', v)} />
                      <TransformSlider label="Z" min="0.1" max="5.0" step="0.1" value={m.s_sz} onChange={v => updateModel('s_sz', v)} />
                    </div>
                  )}
                </div>
              </Expander>

              <Expander title="🎨 Editor de Catálogo de Materiais">
                <select value={matEditName} onChange={(e) => loadMaterialIntoEditor(e.target.value)} className="w-full mb-4 bg-gray-900 border border-gray-700 rounded p-2 text-xs text-white outline-none">
                  {Object.keys(catalog).map(name => <option key={name} value={name}>{name}</option>)}
                </select>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-500 mb-1">Cor HEX</label>
                    <input type="color" value={matEditProps.cor_hex} onChange={e => handleMatPropChange('cor_hex', e.target.value)} className="w-full h-8 rounded cursor-pointer border-0 bg-transparent" />
                  </div>
                  <TransformSlider label="Fosco" min="0" max="1" step="0.05" value={matEditProps.roughness} onChange={v => handleMatPropChange('roughness', v)} />
                  <TransformSlider label="Metálico" min="0" max="1" step="0.05" value={matEditProps.metallic} onChange={v => handleMatPropChange('metallic', v)} />
                  <TransformSlider label="Brilho" min="0" max="1" step="0.05" value={matEditProps.specular} onChange={v => handleMatPropChange('specular', v)} />
                  <TransformSlider label="Vidro" min="0" max="1" step="0.05" value={matEditProps.transmission} onChange={v => handleMatPropChange('transmission', v)} />
                  <TransformSlider label="Cera/Pele" min="0" max="1" step="0.05" value={matEditProps.subsurface} onChange={v => handleMatPropChange('subsurface', v)} />
                </div>
                <button onClick={openSaveMaterialModal} className="w-full py-2 bg-gray-800 hover:bg-gray-700 text-xs font-bold rounded border border-gray-600 transition">💾 Salvar como Novo</button>
              </Expander>

              <Expander title="⚙️ Configs Globais e Perfil Padrão">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                     <span className="text-xs text-gray-400">Perfil Prusa Padrão</span>
                     <select value={m.perfil} onChange={e => updateModel('perfil', e.target.value)} className="w-24 bg-gray-900 border border-gray-700 rounded p-1 text-[10px] text-white outline-none">
                        <option value="020_standard">020_standard</option>
                        <option value="012_fine">012_fine</option>
                     </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Samples Produção</span>
                    <input type="number" value={globalConfig.samples} onChange={e => {setGlobalConfig({...globalConfig, samples: e.target.value}); saveConfigToBackend(catalog);}} className="w-16 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center"/>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Resolução % Produção</span>
                    <input type="number" value={globalConfig.res_producao} onChange={e => {setGlobalConfig({...globalConfig, res_producao: e.target.value}); saveConfigToBackend(catalog);}} className="w-16 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center"/>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Tempo Limite (Segundos)</span>
                    <input type="number" value={globalConfig.max_time} onChange={e => {setGlobalConfig({...globalConfig, max_time: e.target.value}); saveConfigToBackend(catalog);}} className="w-16 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center"/>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Luz Cena</span>
                    <input type="number" step="0.1" value={globalConfig.multiplicador_luz_cena || 1.0} onChange={e => {setGlobalConfig({...globalConfig, multiplicador_luz_cena: parseFloat(e.target.value)}); saveConfigToBackend(catalog);}} className="w-16 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center"/>
                  </div>
                </div>
              </Expander>
            </>
          ) : ( <p className="text-xs text-gray-600 text-center mt-10">Selecione um modelo.</p> )}
        </div>
      </div>

      {/* --- COLUNA DIREITA: AÇÕES E TERMINAL --- */}
      <div className="flex-1 flex flex-col bg-[#0e1117] relative">
        <div className="h-16 border-b border-gray-800 flex items-center justify-end px-6 gap-3 bg-[#16181d] z-20">
           <div className="relative">
             <button onClick={() => setShowPreviewConfig(!showPreviewConfig)} className="bg-gray-800 border border-gray-600 hover:bg-gray-700 text-white p-2 rounded text-sm transition">⚙️</button>
             {showPreviewConfig && (
               <div className="absolute top-full right-0 mt-2 w-64 bg-[#1e2128] border border-gray-600 rounded-lg shadow-2xl p-4 z-50">
                  <h4 className="text-xs font-bold text-gray-400 mb-3 uppercase">Configs do Preview</h4>
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-xs text-gray-300">Resolução %</span>
                    <input type="number" value={globalConfig.prev_res} onChange={e => {setGlobalConfig({...globalConfig, prev_res: e.target.value}); saveConfigToBackend(catalog);}} className="w-14 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center outline-none text-white"/>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-300">Samples</span>
                    <input type="number" value={globalConfig.prev_samples} onChange={e => {setGlobalConfig({...globalConfig, prev_samples: e.target.value}); saveConfigToBackend(catalog);}} className="w-14 bg-gray-900 border border-gray-700 rounded p-1 text-xs text-center outline-none text-white"/>
                  </div>
               </div>
             )}
           </div>

           <button onClick={() => startRender(true)} className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded text-sm font-bold transition shadow-md">📸 Preview Rápido</button>
           <button onClick={() => startRender(false)} className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded text-sm font-bold shadow-[0_0_15px_rgba(37,99,235,0.4)] transition">🚀 INICIAR MATRIZ</button>
        </div>

        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] relative">
           <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-widest flex items-center gap-3">
              👁️ Galeria Visual 
              {isRendering && <span className="text-[10px] text-blue-400 bg-blue-900/30 px-2 py-1 rounded animate-pulse border border-blue-500/50">⏳ Renderizando Motor...</span>}
           </h3>

           {generatedImages.length === 0 ? (
             <div className="flex justify-center items-center h-32 border-2 border-dashed border-gray-800 rounded-xl text-gray-600">A mágica acontece aqui em tempo real.</div>
           ) : (
             <div className="grid grid-cols-2 xl:grid-cols-3 gap-4 pb-16">
                {generatedImages.map((img, i) => (
                  <div key={i} className="bg-[#1e2128] border border-gray-700 rounded-lg overflow-hidden shadow-xl p-2 flex flex-col hover:border-gray-500 transition">
                    <img src={img.url} alt="Render" className="w-full h-auto object-cover rounded bg-black" />
                    <span className="text-[10px] text-center font-bold text-gray-400 mt-2 uppercase tracking-wide">{img.scn} | {img.cam} | {img.mat}</span>
                  </div>
                ))}
             </div>
           )}

           {/* NOVO BOTÃO DE DOWNLOAD EM ZIP */}
           {generatedImages.length > 0 && (
             <button onClick={downloadAllImagesAsZip} className="absolute bottom-6 right-6 bg-green-600 hover:bg-green-500 text-white text-xs font-bold px-5 py-3 rounded-full shadow-[0_0_15px_rgba(22,163,74,0.5)] flex items-center gap-2 z-20 transition hover:scale-105">
               📦 Baixar ZIP
             </button>
           )}
        </div>

        <div className="h-64 bg-black border-t border-gray-800 flex flex-col font-mono relative z-10">
           <div className="flex justify-between items-center px-3 py-1.5 bg-[#16181d] border-b border-gray-800">
             <span className="text-[10px] text-green-500 font-bold">💻 CONSOLE DEBUG (LIVE)</span>
             <div className="flex items-center gap-4">
                <button onClick={downloadLog} title="Baixar log console" className="text-[12px] text-gray-400 hover:text-white transition cursor-pointer">📥</button>
                <button onClick={() => setLogs("")} className="text-[10px] text-gray-500 hover:text-white transition cursor-pointer">Limpar</button>
             </div>
           </div>
           <textarea readOnly value={logs} ref={logEndRef} className="flex-1 w-full bg-transparent text-gray-300 text-[11px] p-3 outline-none resize-none custom-scrollbar" placeholder="Esperando processos..." />
        </div>
      </div>
    </div>
  );
}