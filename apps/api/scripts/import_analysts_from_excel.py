"""
Excel 파일에서 애널리스트 데이터를 가져와 데이터베이스에 등록하는 스크립트
"""
import os
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.analyst import Analyst


def parse_excel_file(file_path: str) -> List[Dict]:
    """
    Excel 파일을 파싱하여 애널리스트 데이터 리스트 반환
    
    Args:
        file_path: Excel 파일 경로
        
    Returns:
        애널리스트 데이터 딕셔너리 리스트
    """
    print(f"Excel 파일 읽는 중: {file_path}")
    
    # 모든 시트 읽기
    excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    
    records = []
    
    for sheet_name, df in excel_data.items():
        print(f"\n시트 '{sheet_name}' 처리 중... (행 수: {len(df)})")
        
        # 컬럼명 정규화 (공백 제거, 소문자 변환)
        df.columns = df.columns.str.strip()
        
        # 가능한 컬럼명 매핑
        column_mapping = {
            'name': ['이름', '애널리스트명', '애널리스트', 'Name', 'name', 'NAME'],
            'firm': ['증권사', '증권사명', '회사', 'Firm', 'firm', 'FIRM', '증권사명'],
            'department': ['부서', '소속부서', 'Department', 'department', 'DEPARTMENT'],
            'sector': ['섹터', '업종', 'Sector', 'sector', 'SECTOR'],
            'email': ['이메일', 'Email', 'email', 'EMAIL', 'E-mail'],
        }
        
        # 컬럼명 찾기
        found_columns = {}
        for target_col, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    found_columns[target_col] = col
                    break
        
        print(f"  발견된 컬럼: {found_columns}")
        
        # 데이터 추출
        for idx, row in df.iterrows():
            record = {}
            
            # 이름과 증권사는 필수
            name = None
            firm = None
            
            if 'name' in found_columns:
                name = row.get(found_columns['name'])
            if 'firm' in found_columns:
                firm = row.get(found_columns['firm'])
            
            # 이름이나 증권사가 없으면 스킵
            if pd.isna(name) or pd.isna(firm) or not str(name).strip() or not str(firm).strip():
                continue
            
            record['name'] = str(name).strip()
            record['firm'] = str(firm).strip()
            
            # 부서
            if 'department' in found_columns:
                dept = row.get(found_columns['department'])
                if not pd.isna(dept) and str(dept).strip():
                    record['department'] = str(dept).strip()
            
            # 섹터 (시트명 또는 컬럼에서)
            sector = None
            if 'sector' in found_columns:
                sector_val = row.get(found_columns['sector'])
                if not pd.isna(sector_val) and str(sector_val).strip():
                    sector = str(sector_val).strip()
            
            # 시트명에서 섹터 추출 시도
            if not sector:
                # 시트명에서 섹터 추출 (예: "반도체", "자동차", "방산", "금융")
                sheet_lower = sheet_name.lower()
                if '반도체' in sheet_name or 'semiconductor' in sheet_lower:
                    sector = '반도체'
                elif '자동차' in sheet_name or 'auto' in sheet_lower or 'automotive' in sheet_lower:
                    sector = '자동차'
                elif '방산' in sheet_name or 'defense' in sheet_lower:
                    sector = '방산'
                elif '금융' in sheet_name or 'finance' in sheet_lower or 'financial' in sheet_lower:
                    sector = '금융'
                else:
                    sector = sheet_name  # 시트명을 그대로 사용
            
            record['sector'] = sector
            
            # 이메일
            if 'email' in found_columns:
                email = row.get(found_columns['email'])
                if not pd.isna(email) and str(email).strip():
                    record['email'] = str(email).strip()
            
            records.append(record)
    
    print(f"\n총 {len(records)}개의 애널리스트 레코드 추출됨")
    return records


def import_analysts(records: List[Dict], db) -> Dict:
    """
    애널리스트 데이터를 데이터베이스에 등록
    
    Args:
        records: 애널리스트 데이터 리스트
        db: 데이터베이스 세션
        
    Returns:
        import 결과 딕셔너리
    """
    total = len(records)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_records = []
    
    print(f"\n데이터베이스에 등록 중... (총 {total}개)")
    
    for idx, record in enumerate(records, 1):
        try:
            # 중복 체크
            existing = db.query(Analyst).filter(
                Analyst.name == record['name'],
                Analyst.firm == record['firm']
            ).first()
            
            if existing:
                print(f"  [{idx}/{total}] 스킵 (중복): {record['name']} - {record['firm']}")
                skipped_count += 1
                continue
            
            # 새 애널리스트 생성
            analyst = Analyst(**record)
            db.add(analyst)
            success_count += 1
            print(f"  [{idx}/{total}] 등록: {record['name']} - {record['firm']} ({record.get('sector', 'N/A')})")
            
        except Exception as e:
            failed_count += 1
            failed_records.append({
                'row': idx,
                'name': record.get('name', 'Unknown'),
                'firm': record.get('firm', 'Unknown'),
                'error': str(e)
            })
            print(f"  [{idx}/{total}] 실패: {record.get('name', 'Unknown')} - {str(e)}")
    
    # 커밋
    try:
        db.commit()
        print(f"\n데이터베이스 커밋 완료!")
    except Exception as e:
        db.rollback()
        print(f"\n데이터베이스 커밋 실패: {str(e)}")
        raise
    
    return {
        'total': total,
        'success': success_count,
        'failed': failed_count,
        'skipped': skipped_count,
        'failed_records': failed_records
    }


def main():
    """메인 함수"""
    # Excel 파일 경로
    excel_file = Path(__file__).parent.parent.parent / "old_assets" / "증권사 리서치센터 애널리스트 리스트(반도체 자동차 방산 금융 최종) (1).xlsx"
    
    if not excel_file.exists():
        print(f"오류: Excel 파일을 찾을 수 없습니다: {excel_file}")
        print("파일 경로를 확인해주세요.")
        sys.exit(1)
    
    # Excel 파일 파싱
    records = parse_excel_file(str(excel_file))
    
    if not records:
        print("경고: 추출된 데이터가 없습니다.")
        sys.exit(1)
    
    # 데이터베이스 연결
    db = SessionLocal()
    
    try:
        # 데이터베이스에 등록
        result = import_analysts(records, db)
        
        # 결과 출력
        print("\n" + "="*60)
        print("등록 결과")
        print("="*60)
        print(f"총 레코드 수: {result['total']}")
        print(f"성공: {result['success']}")
        print(f"실패: {result['failed']}")
        print(f"스킵 (중복): {result['skipped']}")
        
        if result['failed_records']:
            print(f"\n실패한 레코드:")
            for failed in result['failed_records']:
                print(f"  - 행 {failed['row']}: {failed['name']} ({failed['firm']}) - {failed['error']}")
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

