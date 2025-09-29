// alarm_setup.js - Alarm Area Setup UI and logic
(function(){
const style=document.createElement('style');
style.innerHTML = `
#alarmSetup {
    position: absolute;
    top: 20px;
    left: 250px;
    z-index: 1000;
    background: white;
    padding: 10px;
    border-radius: 5px;
    opacity: 0.5;
    font-size:13px;
}
#alarmSetup input[type="file"] { display:inline-block; }
`;
document.head.appendChild(style);

const container=document.createElement('div');
container.id='alarmSetup';
container.innerHTML = `
<h3>警戒範圍設定</h3>
<div>
    <button id="startDrawBtn">設定範圍(滑鼠右鍵封閉範圍)</button><br>
    <button id="downloadGeojsonBtn">下載 GeoJSON</button><br>
    <input type="file" id="uploadGeojsonInput" accept=".json,.geojson"><br>
    <button id="saveAlarmBtn">儲存警戒範圍</button><br>
    <div id="alarmInfo" style="margin-top:6px;font-size:12px;">範圍數量: <span id="alarmCount">0</span></div>
</div>
`;
document.body.appendChild(container);

let alarmAreas = [];
let drawing = false;
let drawPositions = [];
let previewEntity = null;
let drawHandler = null;
let alarmEntityIdCounter = 1;

function updateAlarmCount(){
    const el=document.getElementById('alarmCount');
    if(el) el.textContent = String(alarmAreas.length);
}

function startDrawing(){
    if(drawing) return;
    drawing=true;
    drawPositions=[];
    if(previewEntity){ viewer.entities.remove(previewEntity); previewEntity=null; }
    drawHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    drawHandler.setInputAction(function(click){
        if(!drawing) return;
        const cartesian = viewer.camera.pickEllipsoid(click.position, viewer.scene.globe.ellipsoid);
        if(!cartesian) return;
        const carto = Cesium.Cartographic.fromCartesian(cartesian);
        const lon = Cesium.Math.toDegrees(carto.longitude);
        const lat = Cesium.Math.toDegrees(carto.latitude);
        drawPositions.push(lon, lat);
        if(previewEntity) viewer.entities.remove(previewEntity);
        if(drawPositions.length >= 4){
            previewEntity = viewer.entities.add({
                polyline: {
                    positions: Cesium.Cartesian3.fromDegreesArray(drawPositions),
                    width: 2,
                    material: Cesium.Color.YELLOW
                }
            });
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    drawHandler.setInputAction(function(click){
        if(!drawing) return;
        if(drawPositions.length >= 6){
            const coords=[];
            for(let i=0;i<drawPositions.length;i+=2){ coords.push([drawPositions[i], drawPositions[i+1]]); }
            const first=coords[0];
            const last=coords[coords.length-1];
            if(first[0] !== last[0] || first[1] !== last[1]) coords.push([first[0], first[1]]);
            const flat=[];
            coords.forEach(p => { flat.push(p[0], p[1]); });
            const id = 'alarm-' + (alarmEntityIdCounter++);
            viewer.entities.add({
                id: id,
                polygon: {
                    hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
                    material: Cesium.Color.YELLOW.withAlpha(0.2),
                    outline: true,
                    outlineColor: Cesium.Color.YELLOW
                }
            });
            alarmAreas.push({ id: id, coords: coords });
            updateAlarmCount();
        } else {
            alert('至少需三個點才可建立範圍');
        }
        drawing=false;
        drawPositions=[];
        if(previewEntity){ viewer.entities.remove(previewEntity); previewEntity=null; }
        if(drawHandler){ drawHandler.destroy(); drawHandler=null; }
    }, Cesium.ScreenSpaceEventType.RIGHT_CLICK);
}

const deleteClickHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
deleteClickHandler.setInputAction(function(click){
    if(drawing) return;
    const picked = viewer.scene.pick(click.position);
    if (!Cesium.defined(picked)) return;

    // 支援不同 pick 結構（entity 或 primitive）
    let pickedId = null;
    if (picked.id && typeof picked.id.id === 'string') {
        pickedId = picked.id.id;
    } else if (picked.id && typeof picked.id === 'string') {
        pickedId = picked.id;
    } else if (picked.primitive && picked.primitive.id && typeof picked.primitive.id.id === 'string') {
        pickedId = picked.primitive.id.id;
    }

    if (pickedId && pickedId.startsWith('alarm-')) {
        if (confirm('刪除此範圍?')) {
            // 以 id 移除，確保同步移除 entity
            viewer.entities.removeById(pickedId);
            alarmAreas = alarmAreas.filter(a => a.id !== pickedId);
            updateAlarmCount();
        }
    }
}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

function downloadGeoJSON(){
    const features = alarmAreas.map(a => ({
        type: 'Feature',
        properties: { id: a.id },
        geometry: { type: 'Polygon', coordinates: [ a.coords ] }
    }));
    const geojson = { type: 'FeatureCollection', features: features };
    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'alarm_area.geojson';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

document.getElementById('uploadGeojsonInput').addEventListener('change', function(e){
    const file = e.target.files[0];
    if(!file) return;
    const reader = new FileReader();
    reader.onload = function(){
        try{
            const obj = JSON.parse(reader.result);
            if(obj.type === 'FeatureCollection' && Array.isArray(obj.features)){
                obj.features.forEach(f => {
                    if(f.geometry && f.geometry.type === 'Polygon'){
                        const ring = f.geometry.coordinates[0];
                        const flat = [];
                        const coords = [];
                        ring.forEach(pt => { flat.push(pt[0], pt[1]); coords.push([pt[0], pt[1]]); });
                        const first = coords[0];
                        const last = coords[coords.length -1];
                        if(first[0] !== last[0] || first[1] !== last[1]) coords.push([first[0], first[1]]);
                        const id = 'alarm-' + (alarmEntityIdCounter++);
                        viewer.entities.add({
                            id: id,
                            polygon: {
                                hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
                                material: Cesium.Color.RED.withAlpha(0.2),
                                outline: true,
                                outlineColor: Cesium.Color.RED
                            }
                        });
                        alarmAreas.push({ id: id, coords: coords });
                    }
                });
                updateAlarmCount();
            } else {
                alert('檔案不是 FeatureCollection 格式');
            }
        }catch(err){
            alert('無法解析 GeoJSON: ' + err);
        }
    };
    reader.readAsText(file);
    e.target.value = '';
});

document.getElementById('saveAlarmBtn').addEventListener('click', async function(){
    const features = alarmAreas.map(a => ({
        type: 'Feature',
        properties: { id: a.id },
        geometry: { type: 'Polygon', coordinates: [ a.coords ] }
    }));
    const geojson = { type: 'FeatureCollection', features };
    try{
        const resp = await fetch('/api/save_alarm_area', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(geojson)
        });
        if(resp.ok){
            alert('儲存成功，重新載入頁面以更新圖層');
            location.reload();
        } else {
            const text = await resp.text();
            alert('儲存失敗: ' + resp.status + ' ' + text);
        }
    }catch(err){
        alert('儲存失敗: ' + err);
    }
});

document.getElementById('startDrawBtn').addEventListener('click', startDrawing);
document.getElementById('downloadGeojsonBtn').addEventListener('click', downloadGeoJSON);
updateAlarmCount();

})();