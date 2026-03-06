
Requisitos e Solicitações do Projeto
1. Auto-orientação (Auto Orientation)

A funcionalidade de auto-orientação deve ficar desabilitada por padrão.

Caso seja necessário utilizá-la, ela deve ser explicitamente habilitada por meio de uma flag ou parâmetro.

Portanto:

Default: desativado

Ativação: somente via flag específica

2. Problema de Renderização

Foi identificado um possível problema na renderização gerada pela pipeline atual.

Sintomas observados

Presença de uma linha branca (artefato) no render.

O material preto aparenta estar translúcido, o que não deveria acontecer.

Existe uma faixa visual que não aparece no arquivo do projeto (.blend), e renderizando atraves do blender diretamente a mesma nao aparece.

Observações

No arquivo do projeto gerado, essa faixa não existe, indicando que pode ser um bug no processo de renderização.

Será enviada uma imagem do render para facilitar a análise.

Solicitação

Investigar:

Por que o material preto está aparentando translucidez.

A origem da linha branca / artefato visual.

Se o problema está em:

configuração de material,

pipeline de render,

bug do renderizador,

ou algum outro fator.

3. Organização de Arquivos Gerados

Todos os arquivos gerados pelo sistema devem seguir um padrão de organização por data.

Isso se aplica a:

G-Code

arquivos auto-orientados

imagens renderizadas

quaisquer outros arquivos gerados pelo sistema

Estrutura de diretórios desejada
/ANO
    /MES (Nº - NOME)
        /DIA
            HH_MM_nome-do-arquivo.ext
Exemplo
/2026
    /03 - Março
        /05
            14_32_modeloA.gcode
            14_35_modeloA_render.png
            14_40_modeloA_auto_oriented.stl
Regras

Os arquivos devem conter timestamp no início do nome, no formato:

HH_MM_nome-do-arquivo

Isso facilita:

organização

rastreabilidade

busca de arquivos

diagnóstico posterior.

4. Profile Padrão

Se nenhum profile for especificado pelo usuário, o sistema deve utilizar automaticamente o seguinte profile:

020-standard

Regras:

Esse deve ser o profile padrão global.

Deve ser aplicado somente quando o usuário não definir outro profile explicitamente.

5. Persistência de Configurações no Blender Project

Existe uma dúvida sobre o comportamento atual do sistema.

Situação

Quando o usuário executa um comando especificando algo como:

profile de material preto

configurações relacionadas ao Blender

não está claro se essas configurações estão sendo salvas dentro do Blender Project (.blend).

Solicitação

Caso isso não esteja acontecendo, implementar o seguinte comportamento:

O Blender Project deve salvar todas as configurações relacionadas ao Blender que foram especificadas na execução.

Exemplo

Se o usuário definir:

material: preto

então o material preto deve estar presente e configurado dentro do arquivo .blend gerado.

Objetivo

Isso facilita:

diagnóstico de problemas

inspeção do projeto

reprodutibilidade do resultado

debugging da pipeline.

6. Possível Interface de Pré-visualização (Pergunta)

Essa não é uma solicitação de implementação neste momento, apenas uma avaliação de viabilidade.

Pergunta

Quão difícil seria implementar uma UI simples que mostre uma pré-visualização do modelo renderizado em qualidade muito baixa?

Objetivo dessa UI:

apenas permitir visualizar rapidamente como o resultado está ficando

não precisa ser render de alta qualidade

pode ser algo extremamente simplificado / rápido

Importante

Não é necessário implementar isso agora.

Apenas avaliar se é tecnicamente viável e qual seria o nível de complexidade.