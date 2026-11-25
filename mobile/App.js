import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from 'expo-audio';
import { API_URL } from './config';

const MIN_MS = 3000;
const NAMES = { Health: 'Afya', 'Food Security': 'Chakula', Education: 'Elimu' };

export default function App() {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(recorder);
  const [villages, setVillages] = useState([]);
  const [village, setVillage] = useState(null);
  const [typed, setTyped] = useState('');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      const permission = await AudioModule.requestRecordingPermissionsAsync();
      if (!permission.granted) setMessage('Ruhusa ya kipaza sauti inahitajika.');
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
      try {
        const res = await fetch(`${API_URL}/api/villages`);
        setVillages((await res.json()).villages);
      } catch {
        setMessage('Haiwezi kufikia seva.');
      }
    })();
  }, []);

  const send = async ({ audioUri, text }) => {
    setSending(true);
    setMessage('');
    setResult(null);
    const form = new FormData();
    if (audioUri) form.append('audio', { uri: audioUri, name: 'concern.m4a', type: 'audio/m4a' });
    if (text) form.append('text', text);
    if (village) form.append('village', village);
    try {
      const res = await fetch(`${API_URL}/api/submit`, { method: 'POST', body: form });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || 'error');
      setResult(body);
      setTyped('');
    } catch {
      setMessage('Imeshindwa kutuma. Jaribu tena.');
    }
    setSending(false);
  };

  const start = async () => {
    setMessage('');
    setResult(null);
    await recorder.prepareToRecordAsync();
    recorder.record();
  };

  const stop = async () => {
    const duration = recorderState.durationMillis;
    await recorder.stop();
    if (duration < MIN_MS) {
      setMessage('Tafadhali rekodi angalau sekunde 3.');
      return;
    }
    send({ audioUri: recorder.uri });
  };

  const seconds = Math.floor((recorderState.durationMillis || 0) / 1000);

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Sauti ya Jamii</Text>
      <Text style={styles.subtitle}>Sema wasiwasi wako kwa Kiswahili</Text>

      <Text style={styles.label}>Chagua eneo lako</Text>
      <View style={styles.chips}>
        {villages.map((v) => (
          <Pressable
            key={v}
            onPress={() => setVillage(village === v ? null : v)}
            style={[styles.chip, village === v && styles.chipActive]}
          >
            <Text style={village === v ? styles.chipTextActive : styles.chipText}>{v}</Text>
          </Pressable>
        ))}
      </View>

      <Pressable
        disabled={sending}
        onPress={recorderState.isRecording ? stop : start}
        style={[styles.record, recorderState.isRecording && styles.recording]}
      >
        {sending ? (
          <ActivityIndicator color="#fff" size="large" />
        ) : (
          <Text style={styles.recordText}>{recorderState.isRecording ? `Simamisha ${seconds}s` : 'Rekodi'}</Text>
        )}
      </Pressable>
      <Text style={styles.hint}>
        {sending ? 'Inatuma...' : recorderState.isRecording ? 'Bonyeza tena kusimamisha' : 'Bonyeza kurekodi'}
      </Text>

      {message ? <Text style={styles.error}>{message}</Text> : null}

      {result && (
        <View style={styles.card}>
          <Text style={styles.thanks}>Asante! Wasiwasi wako umepokelewa.</Text>
          <Text style={styles.label}>Ulichosema:</Text>
          <Text style={styles.transcript}>{result.transcript}</Text>
          <Text style={styles.category}>
            Kundi: {NAMES[result.category] || result.category} ({Math.round(result.confidence * 100)}%)
          </Text>
          {result.flagged && <Text style={styles.review}>Mtu atakagua wasiwasi huu.</Text>}
        </View>
      )}

      <Text style={styles.label}>Au andika wasiwasi wako</Text>
      <TextInput
        style={styles.input}
        value={typed}
        onChangeText={setTyped}
        placeholder="Andika hapa"
        multiline
      />
      <Pressable
        disabled={sending || !typed.trim()}
        onPress={() => send({ text: typed.trim() })}
        style={[styles.send, (sending || !typed.trim()) && styles.sendDisabled]}
      >
        <Text style={styles.sendText}>Tuma maandishi</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingTop: 64, alignItems: 'stretch', backgroundColor: '#f9fafb', flexGrow: 1 },
  title: { fontSize: 28, fontWeight: '700', textAlign: 'center', color: '#111827' },
  subtitle: { textAlign: 'center', color: '#6b7280', marginBottom: 24, marginTop: 4 },
  label: { fontWeight: '600', marginTop: 16, marginBottom: 8, color: '#374151' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#fff' },
  chipActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  chipText: { color: '#374151' },
  chipTextActive: { color: '#fff' },
  record: { alignSelf: 'center', width: 150, height: 150, borderRadius: 75, backgroundColor: '#2563eb', alignItems: 'center', justifyContent: 'center', marginTop: 32 },
  recording: { backgroundColor: '#dc2626' },
  recordText: { color: '#fff', fontSize: 20, fontWeight: '600' },
  hint: { textAlign: 'center', color: '#6b7280', marginTop: 12 },
  error: { color: '#b91c1c', textAlign: 'center', marginTop: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginTop: 24, borderWidth: 1, borderColor: '#e5e7eb' },
  thanks: { fontWeight: '700', color: '#15803d', fontSize: 16 },
  transcript: { color: '#111827', fontSize: 16 },
  category: { marginTop: 12, fontWeight: '600', color: '#1d4ed8' },
  review: { marginTop: 8, color: '#92400e' },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#d1d5db', borderRadius: 8, padding: 12, minHeight: 80, textAlignVertical: 'top' },
  send: { backgroundColor: '#111827', borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 12, marginBottom: 32 },
  sendDisabled: { opacity: 0.4 },
  sendText: { color: '#fff', fontWeight: '600' },
});
