-- Schema do Validador Kaltura UNIGRAN
-- Rodar no SQL Editor do Supabase

-- ============================================
-- TABELA: disciplinas (catálogo)
-- ============================================
CREATE TABLE IF NOT EXISTS disciplinas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disc_id TEXT UNIQUE NOT NULL,
  curso_final TEXT NOT NULL,
  disciplina TEXT NOT NULL,
  semestre TEXT NOT NULL,
  professores TEXT[],
  playlist_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disciplinas_disc_id ON disciplinas(disc_id);
CREATE INDEX IF NOT EXISTS idx_disciplinas_curso ON disciplinas(curso_final);

-- ============================================
-- TABELA: videos_kaltura
-- ============================================
CREATE TABLE IF NOT EXISTS videos_kaltura (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disciplina_id UUID REFERENCES disciplinas(id) ON DELETE CASCADE,
  aula INTEGER NOT NULL,
  entry_id TEXT NOT NULL,
  nome_video TEXT,
  embed_url TEXT,
  thumbnail_url TEXT,
  tags TEXT,
  duracao_seg INTEGER,
  kaltura_status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(disciplina_id, aula)
);

CREATE INDEX IF NOT EXISTS idx_videos_disciplina ON videos_kaltura(disciplina_id);
CREATE INDEX IF NOT EXISTS idx_videos_aula ON videos_kaltura(aula);

-- ============================================
-- TABELA: validacoes
-- ============================================
CREATE TABLE IF NOT EXISTS validacoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disciplina_id UUID REFERENCES disciplinas(id) ON DELETE CASCADE,
  aula INTEGER NOT NULL,
  entry_id TEXT,
  embed_url TEXT,
  status_validacao TEXT NOT NULL CHECK (status_validacao IN ('correto', 'corrigido', 'vinculo_errado', 'sem_video', 'pendente')),
  observacao TEXT,
  responsavel TEXT,
  validado_em TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(disciplina_id, aula)
);

CREATE INDEX IF NOT EXISTS idx_validacoes_disciplina ON validacoes(disciplina_id);
CREATE INDEX IF NOT EXISTS idx_validacoes_status ON validacoes(status_validacao);

-- ============================================
-- TABELA: audit_log (opcional, para rastreio)
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT,
  action TEXT NOT NULL,
  table_name TEXT,
  record_id UUID,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_email);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Disciplinas
ALTER TABLE disciplinas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários autenticados podem ler disciplinas"
  ON disciplinas FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Usuários autenticados podem inserir disciplinas"
  ON disciplinas FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Usuários autenticados podem atualizar disciplinas"
  ON disciplinas FOR UPDATE
  TO authenticated
  USING (true);

-- Videos Kaltura
ALTER TABLE videos_kaltura ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários autenticados podem ler vídeos"
  ON videos_kaltura FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Usuários autenticados podem inserir vídeos"
  ON videos_kaltura FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Usuários autenticados podem atualizar vídeos"
  ON videos_kaltura FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Usuários autenticados podem deletar vídeos"
  ON videos_kaltura FOR DELETE
  TO authenticated
  USING (true);

-- Validações
ALTER TABLE validacoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários autenticados podem ler validações"
  ON validacoes FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Usuários autenticados podem inserir validações"
  ON validacoes FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Usuários autenticados podem atualizar validações"
  ON validacoes FOR UPDATE
  TO authenticated
  USING (true);

-- Audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários autenticados podem ler audit log"
  ON audit_log FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Usuários autenticados podem inserir audit log"
  ON audit_log FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- ============================================
-- FUNÇÃO: atualizar updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_disciplinas_updated_at
  BEFORE UPDATE ON disciplinas
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMENTÁRIOS
-- ============================================
COMMENT ON TABLE disciplinas IS 'Catálogo de disciplinas da UNIGRAN EAD';
COMMENT ON TABLE videos_kaltura IS 'Vídeos importados da Kaltura por disciplina/aula';
COMMENT ON TABLE validacoes IS 'Validações humanas dos vínculos vídeo-aula';
COMMENT ON TABLE audit_log IS 'Log de auditoria das ações no sistema';

COMMENT ON COLUMN validacoes.status_validacao IS 'correto: aprovado | corrigido: aprovado com ajuste | vinculo_errado: precisa revisar | sem_video: aula sem vídeo';
