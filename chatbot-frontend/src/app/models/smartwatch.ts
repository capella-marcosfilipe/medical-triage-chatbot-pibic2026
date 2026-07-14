export interface DadosFisiologicos {
  frequencia_cardiaca: number;
  saturacao_oxigenio: number;
  pressao_arterial_sistolica: number;
  pressao_arterial_diastolica: number;
  temperatura_corporal: number;
}

export interface SmartwatchDataResponse {
  dados_fisiologicos: DadosFisiologicos;
}
