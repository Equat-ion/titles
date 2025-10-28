# Copyright (C) 2025 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Stremio Catalog Service for fetching catalog content from installed addons.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from .stremio_addon_service import StremioAddonService


class StremioCatalogService:
    """
    Service for fetching catalogs from Stremio addons.
    Handles fetching catalog content based on addon manifests.
    """
    
    def __init__(self):
        """Initialize the catalog service."""
        self.addon_service = StremioAddonService()
    
    def get_catalogs_for_type(self, content_type: str) -> List[Dict[str, Any]]:
        """
        Get all catalogs for a specific content type from installed addons.
        
        Args:
            content_type (str): Content type to filter by ('movie' or 'series')
        
        Returns:
            list: List of catalog descriptors with addon info and catalog data
        """
        try:
            # Check if user is logged in
            if not self.addon_service.is_logged_in():
                logging.warning('User is not logged in to Stremio - cannot fetch catalogs')
                return []
            
            # Get installed addons
            addons = self.addon_service.get_addon_collection()
            
            catalogs = []
            
            for addon in addons:
                # Skip disabled addons
                if not addon.get('enabled', True):
                    continue
                
                manifest = addon.get('manifest', {})
                transport_url = addon.get('transportUrl', '')
                
                if not manifest or not transport_url:
                    continue
                
                # Check if addon provides catalog resource
                resources = manifest.get('resources', [])
                has_catalog = False
                
                for resource in resources:
                    if isinstance(resource, str) and resource == 'catalog':
                        has_catalog = True
                        break
                    elif isinstance(resource, dict) and resource.get('name') == 'catalog':
                        # Check if this resource supports our content type
                        resource_types = resource.get('types', manifest.get('types', []))
                        if content_type not in resource_types:
                            continue
                        has_catalog = True
                        break
                
                if not has_catalog:
                    continue
                
                # Get catalogs for this content type
                addon_catalogs = manifest.get('catalogs', [])
                
                for catalog in addon_catalogs:
                    catalog_type = catalog.get('type')
                    catalog_id = catalog.get('id')
                    catalog_name = catalog.get('name', 'Unknown Catalog')
                    
                    if catalog_type != content_type:
                        continue
                    
                    # Build catalog descriptor
                    catalog_descriptor = {
                        'addon_name': manifest.get('name', 'Unknown Addon'),
                        'addon_id': manifest.get('id', ''),
                        'catalog_id': catalog_id,
                        'catalog_name': catalog_name,
                        'catalog_type': catalog_type,
                        'transport_url': transport_url,
                        'extra': catalog.get('extra', []),
                    }
                    
                    catalogs.append(catalog_descriptor)
            
            logging.info(f'Found {len(catalogs)} catalogs for type "{content_type}"')
            return catalogs
            
        except Exception as e:
            logging.error(f'Failed to get catalogs for type "{content_type}": {str(e)}')
            return []
    
    def fetch_catalog_content(self, catalog_descriptor: Dict[str, Any], skip: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch content from a specific catalog.
        
        Args:
            catalog_descriptor (dict): Catalog descriptor from get_catalogs_for_type
            skip (int): Number of items to skip for pagination
        
        Returns:
            list: List of meta preview objects from the catalog
        """
        try:
            transport_url = catalog_descriptor['transport_url']
            catalog_type = catalog_descriptor['catalog_type']
            catalog_id = catalog_descriptor['catalog_id']
            
            # Build catalog URL
            base_url = transport_url.rstrip('/')
            if base_url.endswith('/manifest.json'):
                base_url = base_url[:-14]  # Remove /manifest.json
            
            # Build extra params if needed
            extra_params = ''
            if skip > 0:
                extra_params = f'skip={skip}'
            
            if extra_params:
                url = f'{base_url}/catalog/{catalog_type}/{catalog_id}/{extra_params}.json'
            else:
                url = f'{base_url}/catalog/{catalog_type}/{catalog_id}.json'
            
            logging.debug(f'Fetching catalog from: {url}')
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logging.warning(f'Failed to fetch catalog from {url}: status {response.status_code}')
                return []
            
            data = response.json()
            metas = data.get('metas', [])
            
            logging.info(f'Fetched {len(metas)} items from catalog "{catalog_descriptor["catalog_name"]}"')
            
            return metas
            
        except Exception as e:
            logging.warning(f'Error fetching catalog content: {str(e)}')
            return []
    
    def fetch_all_catalogs_for_type(self, content_type: str, max_items_per_catalog: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch content from all catalogs for a specific content type.
        
        Args:
            content_type (str): Content type to filter by ('movie' or 'series')
            max_items_per_catalog (int): Maximum number of items to fetch per catalog
        
        Returns:
            list: List of catalog sections, each containing catalog info and items
        """
        catalogs = self.get_catalogs_for_type(content_type)
        
        catalog_sections = []
        
        for catalog in catalogs:
            items = self.fetch_catalog_content(catalog)
            
            # Limit items per catalog
            items = items[:max_items_per_catalog]
            
            if items:
                section = {
                    'catalog_name': catalog['catalog_name'],
                    'addon_name': catalog['addon_name'],
                    'catalog_id': catalog['catalog_id'],
                    'items': items,
                }
                catalog_sections.append(section)
        
        return catalog_sections
