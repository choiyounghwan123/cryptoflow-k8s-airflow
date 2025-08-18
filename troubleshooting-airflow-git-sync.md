# Airflow Git Sync DAG 인식 문제 해결 과정

## 🔍 발생한 문제들

### 1. 재귀 디렉토리 루프 에러
```
RuntimeError: Detected recursive loop when walking DAG directory /opt/airflow/dags: 
/opt/airflow/dags/dags/2e8ee9bfbe117b5f4195cc7b6d13f7e871ce890d has appeared more than once.
```

### 2. DB 초기화 에러
```
ERROR: You need to initialize the database. Please run `airflow db init`.
```

### 3. Fernet 키 에러
```
airflow.exceptions.AirflowException: Could not create Fernet object: 
Fernet key must be 32 url-safe base64-encoded bytes.
```

### 4. DAG 파일 인식 안됨
- Git Sync는 정상 동작하지만 Airflow가 DAG 파일을 찾지 못함

## 🛠 해결 과정

### 1단계: Fernet 키 수정
**문제**: 잘못된 base64 인코딩과 길이
```yaml
# 이전 (잘못된 키)
fernet-key: Zm9vYmFyZm9vYmFyZm9vYmFyZm9vYmFyZm9vYFyZm9vYg==

# 수정 (올바른 32바이트 키)  
fernet-key: UEJiQ2M2dlVJOVNNdHRvTnVMTEV5TzFjWnN3WkNCMzQ=
```

### 2단계: DB 연결 환경변수 추가
**문제**: 스케줄러와 웹서버에 PostgreSQL 연결 정보 누락

**스케줄러 (`airflow-scheduler-deployment.yaml`)**:
```yaml
env:
- name: AIRFLOW__CORE__FERNET_KEY
  valueFrom:
    secretKeyRef:
      name: airflow-secret
      key: fernet-key
# PostgreSQL 연결 정보 추가
- name: POSTGRES_USER
  valueFrom:
    secretKeyRef:
      name: airflow-secret
      key: postgres-user
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: airflow-secret
      key: postgres-password
- name: POSTGRES_DB
  valueFrom:
    secretKeyRef:
      name: airflow-secret
      key: postgres-db
- name: AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
  value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgresql-service:5432/$(POSTGRES_DB)"
```

**웹서버 (`airflow-webserver-deployment.yaml`)**:
- 동일한 환경변수 추가

### 3단계: Git Sync와 DAG 경로 설정
**문제**: Git Sync가 생성하는 디렉토리 구조와 Airflow DAG 경로 불일치

**최종 해결책**:
1. **Git Sync 설정**: `GIT_SYNC_DEST` 제거 (전체 리포지토리 동기화)
2. **볼륨 마운트**: 전체 Git 디렉토리를 별도 경로에 마운트
3. **DAG 폴더 경로**: ConfigMap에서 정확한 경로 지정

```yaml
# 스케줄러 볼륨 마운트
volumeMounts:
- name: dags-volume
  mountPath: /opt/airflow/git-dags
  readOnly: true

# Git Sync 설정 (GIT_SYNC_DEST 제거)
- name: GIT_SYNC_REPO
  value: "git@github.com:choiyounghwan123/cryptoflow-k8s-airflow.git"
- name: GIT_SYNC_BRANCH
  value: "main"
- name: GIT_SYNC_ROOT
  value: "/tmp/git"
# GIT_SYNC_DEST 제거 - 전체 리포지토리 동기화
```

```yaml
# ConfigMap에서 DAG 폴더 경로 지정
AIRFLOW__CORE__DAGS_FOLDER: "/opt/airflow/git-dags/cryptoflow-k8s-airflow.git/dags"
```

## 📁 최종 디렉토리 구조

```
/opt/airflow/git-dags/
├── .git/
├── 2e8ee9bfbe117b5f4195cc7b6d13f7e871ce890d/  # 실제 커밋 폴더
│   ├── coincap_collector.py
│   ├── dags/
│   │   └── test_git_sync.py  # 실제 DAG 파일
│   └── k8s/
└── cryptoflow-k8s-airflow.git -> 2e8ee9bfbe117b5f4195cc7b6d13f7e871ce890d  # 심볼릭 링크
```

**Airflow DAG 경로**: `/opt/airflow/git-dags/cryptoflow-k8s-airflow.git/dags/`

## 🎯 핵심 포인트

1. **Fernet 키**: 반드시 올바른 32바이트 base64 인코딩 필요
2. **DB 연결**: 모든 Airflow 컴포넌트에 PostgreSQL 연결 정보 필요
3. **Git Sync 경로**: 심볼릭 링크와 실제 디렉토리 구조 이해 필요
4. **subPath 제한**: Kubernetes subPath는 심볼릭 링크를 잘 처리하지 못함

## 🚀 배포 순서

1. **PostgreSQL** 시작
2. **DB Init Job** 실행 (완료될 때까지 대기)
3. **Airflow 스케줄러/웹서버** 시작

## ✅ 확인 방법

```bash
# DAG 파일 확인
kubectl exec deployment/airflow-scheduler -n airflow -c airflow-scheduler -- \
  ls -la /opt/airflow/git-dags/cryptoflow-k8s-airflow.git/dags/

# 스케줄러 로그 확인
kubectl logs deployment/airflow-scheduler -n airflow -c airflow-scheduler --tail=20

# Pod 상태 확인
kubectl get pods -n airflow
```

## 📝 주요 파일 변경사항

### `k8s/airflow/airflow-secret.yaml`
- 올바른 Fernet 키로 수정

### `k8s/airflow/airflow-scheduler-deployment.yaml`
- PostgreSQL 연결 환경변수 추가
- Git 볼륨 마운트 경로 변경 (`/opt/airflow/git-dags`)
- `GIT_SYNC_DEST` 제거

### `k8s/airflow/airflow-webserver-deployment.yaml`
- PostgreSQL 연결 환경변수 추가

### `k8s/airflow/airflow-config.yaml`
- DAG 폴더 경로 지정: `/opt/airflow/git-dags/cryptoflow-k8s-airflow.git/dags`

### `k8s/airflow/airflow-db-init-job.yaml`
- Secret 참조를 `airflow-secret`으로 통일

이제 `test_git_sync` DAG가 Airflow 웹 UI에서 정상적으로 표시됩니다! 🎉
