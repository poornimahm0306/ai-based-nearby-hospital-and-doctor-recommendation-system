import React, { useState } from "react";
import axios from "axios";

export default function App() {
  const [lat, setLat] = useState(28.6139);
  const [lon, setLon] = useState(77.2090);
  const [query, setQuery] = useState("heart pain");
  const [specialty, setSpecialty] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/recommend", {
        latitude: lat,
        longitude: lon,
        query,
        specialty,
        max_distance_km: 20,
        limit: 10
      });
      setResults(res.data.recommendations || []);
    } catch (e) {
      console.error(e);
      alert("Search failed (check backend logs)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Nearby Hospital & Doctor Recommendation</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <input className="p-2 rounded border" value={lat} onChange={(e)=>setLat(Number(e.target.value))} placeholder="Latitude" />
        <input className="p-2 rounded border" value={lon} onChange={(e)=>setLon(Number(e.target.value))} placeholder="Longitude" />
        <input className="col-span-2 p-2 rounded border" value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Symptoms or query" />
        <input className="col-span-2 p-2 rounded border" value={specialty} onChange={(e)=>setSpecialty(e.target.value)} placeholder="Specialty (optional)" />
      </div>

      <div className="flex gap-2 mb-6">
        <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={search}>{loading ? "Searching..." : "Search"}</button>
      </div>

      <div>
        {results.length === 0 && <p className="text-sm text-gray-600">No results yet — try a search.</p>}
        {results.map(r => (
          <div key={r.id} className="bg-white p-4 rounded shadow mb-3">
            <div className="flex justify-between">
              <div>
                <h3 className="text-lg font-medium">{r.name}</h3>
                <p className="text-sm text-gray-600">{r.specialty} • {r.type}</p>
                <p className="text-sm text-gray-500">{r.address}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">{r.rating} ★</p>
                <p className="text-sm text-gray-600">{r.distance_km} km</p>
              </div>
            </div>
            <div className="mt-2 text-sm text-gray-700">
              <p>Match score: {r.match_score}</p>
              <p>Semantic: {r.semantic_score} • Distance: {r.distance_score}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
