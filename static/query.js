// query.js - 將 ships_map.html 中的查詢 UI 與功能搬移到此檔

(function() {
    // 新增查詢樣式
    const style = document.createElement('style');
    style.innerHTML = `
.degInput {
    width: 130px;
}
#queryInfo {
    position: absolute;
    top: 20px;
    left: 20px;
    z-index: 1000;
    background: white;
    padding: 10px;
    border-radius: 5px;
    opacity: 0.5;
}
`;
    document.head.appendChild(style);

    // 建立查詢面板 DOM
    const container = document.createElement('div');
    container.id = 'queryInfo';
    container.innerHTML = `
<h3>船舶查詢</h3>
<label>船名: <input type="text" id="shipname" style="width: 162px;"></label><br>
<label>最小緯度: <input class="degInput" type="number" id="minLat" step="0.1" value="23"></label><br>
<label>最大緯度: <input class="degInput" type="number" id="maxLat" step="0.1" value="30"></label><br>
<label>最小經度: <input class="degInput" type="number" id="minLon" step="0.1" value="110"></label><br>
<label>最大經度: <input class="degInput" type="number" id="maxLon" step="0.1" value="125"></label><br>
<label>開始時間: <br><input type="datetime-local" id="start" value=""></label><br>
<label>結束時間: <br><input type="datetime-local" id="end" value=""></label><br>
<button id="queryBtn">查詢</button>
`;
    document.body.appendChild(container);

    function toDatetimeLocalString(date) {
        return date.toISOString().slice(0, 16);
    }
    function setDefaultTimeRange() {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        document.getElementById('start').value = toDatetimeLocalString(oneHourAgo);
        document.getElementById('end').value = toDatetimeLocalString(now);
    }

    // getArrowPolyline 已從 ships_map.html 移入此處
    function getArrowPolyline(longitude, latitude, heading, length) {
        // Convert heading to radians and calculate the base position
        const headingRad = Cesium.Math.toRadians(90 - heading);
        const baseLength = (1 / 7) * length;

        const baseLongitude = longitude - (baseLength * Math.cos(headingRad)) / (111320 * Math.cos(Cesium.Math.toRadians(latitude)));
        const baseLatitude = latitude - (baseLength * Math.sin(headingRad)) / 110540;

        // Calculate the coordinates for the arrow wings
        const angle = 165;
        const leftWingLongitude = longitude + (length * 0.2 * Math.cos(headingRad + Cesium.Math.toRadians(angle))) / (111320 * Math.cos(Cesium.Math.toRadians(latitude)));
        const leftWingLatitude = latitude + (length * 0.2 * Math.sin(headingRad + Cesium.Math.toRadians(angle))) / 110540;

        const rightWingLongitude = longitude + (length * 0.2 * Math.cos(headingRad - Cesium.Math.toRadians(angle))) / (111320 * Math.cos(Cesium.Math.toRadians(latitude)));
        const rightWingLatitude = latitude + (length * 0.2 * Math.sin(headingRad - Cesium.Math.toRadians(angle))) / 110540;

        return {
            positions: Cesium.Cartesian3.fromDegreesArray(
                [
                    longitude, latitude, // Tip of the arrow
                    leftWingLongitude, leftWingLatitude, // Left wing of the arrow
                    baseLongitude, baseLatitude, // Base of the arrow
                    rightWingLongitude, rightWingLatitude, // Right wing of the arrow
                    longitude, latitude, // Tip of the arrow
                ]
            ),
            width: 3,
            material: Cesium.Color.RED,
            clampToGround: true,
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                0.0,
                30000000.0
            )
        };
    }

    async function loadShipsData() {
        try {
            const shipname = document.getElementById('shipname').value;
            console.log('Fetching data for shipname:', shipname);

            const startTime = document.getElementById('start').value;
            const endTime = document.getElementById('end').value;
            const minLat = document.getElementById('minLat').value;
            const maxLat = document.getElementById('maxLat').value;
            const minLon = document.getElementById('minLon').value;
            const maxLon = document.getElementById('maxLon').value;

            const queryParams = new URLSearchParams();
            if (shipname) queryParams.set('shipname', shipname);
            if (startTime && endTime) {
                queryParams.set('start', startTime.replace('T', ' ') + '.000');
                queryParams.set('end', endTime.replace('T', ' ') + '.000');
            }
            if (minLat && maxLat) {
                queryParams.set('min_lat', minLat);
                queryParams.set('max_lat', maxLat);
            }
            if (minLon && maxLon) {
                queryParams.set('min_lon', minLon);
                queryParams.set('max_lon', maxLon);
            }

            const response = await fetch(`/api/ais/history?${queryParams.toString()}`);
            const data = await response.json();

            viewer.entities.removeAll();

            Object.values(data).forEach(ship => {
                const position = Cesium.Cartesian3.fromDegrees(ship.lon, ship.lat);

                const arrowLength = 10 + ship.speed * 100; // 航速影響箭頭長度

                viewer.entities.add({
                    position: position,
                    polyline: getArrowPolyline(ship.lon, ship.lat, parseFloat(ship.course), arrowLength),
                    label: {
                        text: ship.shipname,
                        font: '14px sans-serif',
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        outlineWidth: 2,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -32),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY,
                        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                            0.0,
                            500000.0
                        )
                    },
                    description: `
                        <table>
                            <tr><td>船名:</td><td>${ship.shipname}</td></tr>
                            <tr><td>速度:</td><td>${ship.speed} 節</td></tr>
                            <tr><td>航向:</td><td>${ship.course}°</td></tr>
                            <tr><td>目的地:</td><td>${ship.destination}</td></tr>
                            <tr><td>船舶類型:</td><td>${ship.shiptype}</td></tr>
                            <tr><td>最後更新:</td><td>${new Date(ship.timestamp).toLocaleString()}</td></tr>
                        </table>
                    `
                });
            });

            viewer.zoomTo(viewer.entities);

        } catch (error) {
            console.error('Error loading ships data:', error);
        }
    }

    document.getElementById('queryBtn').addEventListener('click', loadShipsData);
    setDefaultTimeRange();
    loadShipsData();
    setInterval(loadShipsData, 60000);

})();